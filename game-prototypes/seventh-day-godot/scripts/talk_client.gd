extends Node
## TalkClient —— 自由对话网络层（还原LLM F1）
## 复用网页版 server.js 的 /api/talk 和 /api/endgame（本地起一个 Node 服务即可）
##
## 用法（异步，await 等待）：
##   var res: Dictionary = await TalkClient.talk(body)
##   var epi: Dictionary = await TalkClient.endgame(body)
## 任何网络失败都会返回 {"offline": true}，调用方要自己兜底（罐头回复）。
## BASE_URL 可以运行时改（测试时指向 mock 服务器）。

# 还原LLM G1：后端地址可配置 —— project.godot 的 [llm] base_url（默认本机 8890）
# 注意：get_setting 返回 Variant，显式标注 : String 保持类型纪律
# （项目当前未在 project.godot 开启"警告当错误"，但代码按该标准写）
var BASE_URL: String = ProjectSettings.get_setting("llm/base_url", "http://127.0.0.1:8890")

var _http: HTTPRequest

func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 20.0        # 20 秒：LLM 生成回复可能 8~20 秒，别掐断正常回复；
								# 服务器没起时会立即 connection-refused（本地 RST），不会真等满 20 秒
	add_child(_http)

# 自由对话：body 用 LLMMapper.build_talk_body(...) 生成
func talk(body: Dictionary) -> Dictionary:
	return await _post("/api/talk", body)

# 无限结局：body 含 finalLine / ending / worldState / reputation / authorConfessed
func endgame(body: Dictionary) -> Dictionary:
	return await _post("/api/endgame", body)

func _post(path: String, body: Dictionary) -> Dictionary:
	var err := _http.request(BASE_URL + path, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify(body))
	if err != OK:
		return { "offline": true, "error": "request_failed" }
	# await 信号会把 4 个参数打包成数组：result, response_code, headers, body
	var result: Array = await _http.request_completed
	var response_code: int = result[1]
	var response_body: PackedByteArray = result[3]
	if response_code != 200:
		return { "offline": true, "error": "http_%d" % response_code }
	var parsed: Variant = JSON.parse_string(response_body.get_string_from_utf8())
	if parsed is Dictionary:
		return parsed
	return { "offline": true, "error": "bad_json" }
