import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:mime/mime.dart';

class ApiService {
  final String baseUrl = "http://192.168.1.115:5000"; // FastAPI 서버 주소
  final Duration timeoutDuration = const Duration(seconds: 60); // 기본 타임아웃 60초

  Future<Map<String, dynamic>> sendChat({
    File? file,
    required String message,
    Duration? customTimeout, // ✅ 요청마다 타임아웃 유연화
  }) async {
    var uri = Uri.parse("$baseUrl/chat/stream");
    var request = http.MultipartRequest("POST", uri);

    // 메시지 필드 추가
    request.fields["message"] = message;

    // 파일 첨부
    if (file != null) {
      final mimeType = lookupMimeType(file.path) ?? "application/octet-stream";
      print("선택한 파일 MIME 타입: $mimeType");

      request.files.add(await http.MultipartFile.fromPath(
        "file",
        file.path,
        contentType: MediaType.parse(mimeType),
      ));
    }

    // ✅ 헤더 확장성 확보
    request.headers.addAll({
      "Accept": "application/json",
      // 필요 시 인증 토큰 추가 가능
      // "Authorization": "Bearer <token>",
    });

    var client = http.Client();
    try {
      // ✅ 타임아웃 적용
      var streamedResponse = await client.send(request).timeout(customTimeout ?? timeoutDuration);
      var responseBody = await streamedResponse.stream.bytesToString();

      if (streamedResponse.statusCode != 200) {
        throw Exception("서버 오류 발생 (코드: ${streamedResponse.statusCode})");
      }

      // ✅ JSON 파싱 오류 처리
      try {
        return jsonDecode(responseBody);
      } catch (e) {
        throw Exception("응답 파싱 오류: $e\n원본 응답: $responseBody");
      }
    } on SocketException {
      throw Exception("네트워크 연결 오류: 서버에 연결할 수 없습니다.");
    } on http.ClientException catch (e) {
      throw Exception("HTTP 클라이언트 오류: $e");
    } on TimeoutException {
      throw Exception("요청 시간이 초과되었습니다. (${(customTimeout ?? timeoutDuration).inSeconds}초)");
    } finally {
      client.close();
    }
  }
}
