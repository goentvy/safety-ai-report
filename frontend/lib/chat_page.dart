import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'api_service.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final ApiService apiService = ApiService();
  final TextEditingController _controller = TextEditingController();
  File? _selectedImage;
  String _response = "";
  bool _isLoading = false; // ✅ 로딩 상태 관리

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);

    if (pickedFile != null) {
      setState(() {
        _selectedImage = File(pickedFile.path);
      });
    }
  }

  Future<void> _sendMessage() async {
    setState(() {
      _isLoading = true;   // ✅ 요청 시작 시 로딩 표시
      _response = "";
    });

    try {
      final result = await apiService.sendChat(
        file: _selectedImage,
        message: _controller.text,
      );

      print("서버 응답 전체: $result");

      setState(() {
        if (result["status"] == "success") {
          _response = result["content"] ?? "응답 없음";
        } else {
          // ✅ 사용자 친화적 에러 메시지
          _response = "⚠️ 분석 중 오류가 발생했습니다.\n"
              "잠시 후 다시 시도해주세요.";
        }
      });
    } catch (e) {
      setState(() {
        // ✅ 사용자 친화적 에러 메시지
        _response = "⚠️ 서버와 통신 중 문제가 발생했습니다.\n"
            "네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요.\n\n"
            "세부 정보: $e"; // 개발자 디버깅용
      });
    } finally {
      setState(() {
        _isLoading = false; // ✅ 요청 종료 시 로딩 해제
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Safety AI Agent")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              keyboardType: TextInputType.text,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _sendMessage(),
              decoration: const InputDecoration(labelText: "메시지 입력"),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                ElevatedButton(
                  onPressed: _pickImage,
                  child: Text(_selectedImage == null ? "사진 선택" : "이미지 선택됨"),
                ),
                const SizedBox(width: 10),
                ElevatedButton(
                  onPressed: _sendMessage,
                  child: const Text("전송"),
                ),
              ],
            ),
            const SizedBox(height: 10),
            if (_selectedImage != null)
              Padding(
                padding: const EdgeInsets.only(top: 10),
                child: Image.file(_selectedImage!, height: 120),
              ),
            const SizedBox(height: 20),
            Expanded(
              child: _isLoading
                  ? const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(), // ✅ 로딩 스피너
                    SizedBox(height: 10),
                    Text("분석을 진행 중입니다... 잠시만 기다려주세요."),
                  ],
                ),
              )
                  : SingleChildScrollView(
                child: SelectableText(
                  _response,
                  style: const TextStyle(fontSize: 16),
                  textAlign: TextAlign.start,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
