extends Node
## 第十九课：程序化音效 —— 不用音频文件，用代码合成声音
##
## 新招：
##   1. 采样原理 —— 每秒 44100 个采样点，每个点是一个正弦值 sin(2π·频率·t)
##   2. AudioStreamWAV —— 把这段"采样数组"塞进内存，直接当声音播
##   3. 合成钟声 —— 基频 + 非整数倍泛音（钟的音色），指数衰减（越敲越轻）
##   4. 合成底噪 —— 超低频 + 纯五度 + 慢速起伏，循环播放当氛围
##   5. AudioStreamPlayer —— 播一段内存里的声音（不需要 .wav 文件）
##
## 用法：Sound.play_bell()（钟响）、Sound.play_tick()（对话翻页）
## 环境底噪启动即自动循环，音量调低。

const SR := 44100

var _bell: AudioStreamWAV
var _tick: AudioStreamWAV
var _bell_player: AudioStreamPlayer
var _tick_player: AudioStreamPlayer

func _ready() -> void:
	_bell = _gen_bell()
	_tick = _gen_tick()
	_bell_player = AudioStreamPlayer.new()
	_bell_player.stream = _bell
	add_child(_bell_player)
	_tick_player = AudioStreamPlayer.new()
	_tick_player.stream = _tick
	add_child(_tick_player)
	# 氛围底噪：循环播放，音量调低
	var drone := AudioStreamPlayer.new()
	drone.stream = _gen_drone()
	drone.volume_db = -20.0
	add_child(drone)
	drone.play()

func play_bell() -> void:
	_bell_player.play()

func play_tick() -> void:
	_tick_player.play()

# ---- 合成钟声 ----
# 基频 196Hz(G3) + 钟式泛音：频率是基频的 2.0 / 2.9 / 4.1 / 5.4 倍。
# 普通乐器是整数倍泛音（干净），钟是"非整数倍"泛音，才有那种空灵发散的"铛——"。
# 包络：起音 12ms 冲上去，再按 e^(-3.2t) 慢慢衰减，总共 2.5 秒。
func _gen_bell() -> AudioStreamWAV:
	var dur := 2.5
	var n := int(SR * dur)
	var buf := PackedByteArray()
	buf.resize(n * 2)
	var partials := [
		[1.0, 196.0, 0.50],
		[2.0, 392.0, 0.25],
		[2.9, 568.4, 0.18],
		[4.1, 803.6, 0.10],
		[5.4, 1058.4, 0.06],
	]
	for i in n:
		var t := float(i) / SR
		var env := exp(-3.2 * t) * (1.0 - exp(-90.0 * t))
		var s := 0.0
		for p in partials:
			s += p[2] * sin(TAU * p[1] * t)
		_write_sample(buf, i, s * env * 0.35)
	return _make_stream(buf, n)

# ---- 合成翻页声 ----
# 50ms 的短促高音，指数衰减到没——"嘀"一下，翻页/选选项时用。
func _gen_tick() -> AudioStreamWAV:
	var dur := 0.05
	var n := int(SR * dur)
	var buf := PackedByteArray()
	buf.resize(n * 2)
	for i in n:
		var t := float(i) / SR
		var s := 0.4 * sin(TAU * 1320.0 * t) * exp(-70.0 * t)
		_write_sample(buf, i, s)
	return _make_stream(buf, n)

# ---- 合成环境底噪 ----
# 55Hz(低音A) + 82.5Hz(上方纯五度)，叠一层 8 秒周期的慢起伏，循环 4 秒。
# 4 秒整 = 55Hz 的 220 个周期 + 82.5Hz 的 330 个周期，首尾相位刚好接上，循环不咔哒。
func _gen_drone() -> AudioStreamWAV:
	var dur := 4.0
	var n := int(SR * dur)
	var buf := PackedByteArray()
	buf.resize(n * 2)
	for i in n:
		var t := float(i) / SR
		var lfo := 0.6 + 0.4 * sin(TAU * 0.125 * t)
		var s := 0.16 * sin(TAU * 55.0 * t) + 0.10 * sin(TAU * 82.5 * t)
		_write_sample(buf, i, s * lfo)
	var stream := _make_stream(buf, n)
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_begin = 0
	stream.loop_end = n
	return stream

# 把采样数组打包成可播的 AudioStreamWAV
func _make_stream(buf: PackedByteArray, n: int) -> AudioStreamWAV:
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = SR
	stream.stereo = false
	stream.data = buf
	return stream

# 浮点音量 [-1,1] → 16 位整数采样（小端序：低字节在前，高字节在后）
func _write_sample(buf: PackedByteArray, i: int, v: float) -> void:
	var sample := int(round(clampf(v, -1.0, 1.0) * 32767.0))
	buf[i * 2] = sample & 0xFF
	buf[i * 2 + 1] = (sample >> 8) & 0xFF
