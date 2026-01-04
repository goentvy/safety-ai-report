import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:mime/mime.dart';

class ApiService {
  final String baseUrl = "http://192.168.1.115:5000"; // FastAPI 서버 주소

  Future<Map<String, dynamic>> sendChat({
    File? file,
    required String message,
  }) async {
    var uri = Uri.parse("$baseUrl/chat");
    var request = http.MultipartRequest("POST", uri);

    request.fields["message"] = message;

    if (file != null) {
      final mimeType = lookupMimeType(file.path) ?? "application/octet-stream";
      print("선택한 파일 MIME 타입: $mimeType");

      request.files.add(await http.MultipartFile.fromPath(
        "file",
        file.path,
        contentType: MediaType.parse(mimeType),
      ));
    }

    var response = await request.send();
    var responseBody = await response.stream.bytesToString();

    if (response.statusCode != 200) {
      throw Exception("서버 오류: ${response.statusCode}, 응답: $responseBody");
    }

    return jsonDecode(responseBody);
  }
}
