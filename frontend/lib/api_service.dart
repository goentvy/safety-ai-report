import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

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
      request.files.add(await http.MultipartFile.fromPath("file", file.path));
    }

    var response = await request.send();
    var responseBody = await response.stream.bytesToString();

    return jsonDecode(responseBody);
  }
}
