import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:image_picker/image_picker.dart';
import 'api_service.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});
  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final ApiService api = ApiService();
  final TextEditingController _controller = TextEditingController();
  String? responseType;
  String? responseContent;
  File? selectedImage;

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);

    if (pickedFile != null) {
      setState(() {
        selectedImage = File(pickedFile.path);
      });
    }
  }

  Future<void> _sendMessage() async {
    var result = await api.sendChat(
      message: _controller.text,
      file: selectedImage,
    );
    setState(() {
      responseType = result["type"];
      responseContent = result["content"];
    });
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
              decoration: const InputDecoration(
                labelText: "메시지 입력",
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                ElevatedButton(
                  onPressed: _pickImage,
                  child: const Text("사진 선택"),
                ),
                const SizedBox(width: 10),
                if (selectedImage != null)
                  Text("이미지 선택됨 ✅", style: TextStyle(color: Colors.green)),
              ],
            ),
            const SizedBox(height: 10),
            ElevatedButton(
              onPressed: _sendMessage,
              child: const Text("전송"),
            ),
            const SizedBox(height: 20),
            if (responseContent != null)
              Expanded(
                child: responseType == "document"
                    ? Markdown(data: responseContent!)
                    : SingleChildScrollView(
                  child: Text(responseContent!),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
