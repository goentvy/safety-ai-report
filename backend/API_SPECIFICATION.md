# 🔌 Safety AI Agent - API 명세서 (Flutter/Dart Team)

**버전:** 2.2.0 (JSON 버퍼링 스트리밍)  
**마지막 업데이트:** 2026년 1월 10일  
**프론트엔드:** Flutter/Dart  
**상태:** ✅ 프로덕션 준비 완료

---

## 📋 목차

1. [개요](#개요)
2. [기본 정보](#기본-정보)
3. [API 엔드포인트](#api-엔드포인트)
4. [스트리밍 응답](#스트리밍-응답)
5. [요청/응답 스키마](#요청응답-스키마)
6. [에러 처리](#에러-처리)
7. [코드 예시](#코드-예시)

---

## 개요

### 서비스 설명

Safety AI Agent는 **실시간 스트리밍** 기반으로:
- 산업현장 사진을 자동으로 분석
- 산업안전보건법 위반사항 지적
- 안전 관련 질문에 법령 기반 답변

### 핵심 특징

| 특징 | 설명 |
|------|------|
| 🚀 실시간 스트리밍 | SSE 기반 청크 전송 |
| ⚡ 빠른 응답 | 첫 응답 < 200ms |
| 💾 최적화 | 40% 토큰 감소 |
| 🛡️ 검증 | 입력 검증 및 에러 처리 |

### 기본 URL

```
개발 환경: http://localhost:8000
스테이징:  https://staging-api.example.com
프로덕션: https://api.example.com
```

---

## 기본 정보

### 요청 헤더

```
Content-Type: multipart/form-data (이미지 업로드 시)
Accept: text/event-stream (스트리밍 응답 시)
```

### 응답 형식

**SSE (Server-Sent Events)** 스트림:
```
data: 첫번째청크\n\n
data: 두번째청크\n\n
data: 세번째청크\n\n
```

### 파일 제한

- **최대 크기**: 10MB
- **지원 형식**: JPEG, PNG, GIF, WebP

---

## API 엔드포인트

### 1. 헬스체크

```
GET /
```

**목적**: 서버 상태 확인

**응답**:
```json
{
  "status": "healthy",
  "service": "Safety AI Agent",
  "version": "2.1.0",
  "streaming": true
}
```

---

### 2. 통합 스트리밍 API ⭐ (권장)

```
POST /chat/stream
```

**목적**: 이미지 분석, 문서 생성, 질의응답을 스트리밍으로 처리

**파라미터**:

| 파라미터 | 타입 | 필수 | 설명 | 예시 |
|---------|------|------|------|------|
| `file` | File | ❌ | 분석할 이미지 (최대 10MB) | `photo.jpg` |
| `message` | string | ❌ | 질문 또는 요청 | "비계의 안전성을 점검해줘" |

**최소 요구사항**: `file` 또는 `message` 중 하나는 필수

**응답**: 스트림 형식 (SSE)

---

## 스트리밍 응답

### 응답 형식 (JSON 버퍼링)

**개선된 스트리밍**: 50~60자 단위로 버퍼링된 JSON 응답

```json
data: {"type":"text","content":"비계 점검 결과:\n## 1. 보호구"}
data: {"type":"text","content":" 착용 여부\n- 안전모: 미착용 (위반)"}
data: {"type":"text","content":"\n\n## 2. 난간대 높이\n- 현황: 85cm"}
data: {"type":"text","content":"\n- 기준: 90cm 이상\n- 판정: 부적합"}
```

### Flutter/Dart 구현 (http 패키지)

#### 1. 의존성 추가 (pubspec.yaml)

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  image_picker: ^1.0.0  # 이미지 선택용
```

#### 2. SSE 스트리밍 처리

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class SafetyApiService {
  static const String baseUrl = 'http://localhost:8000';
  
  /// SSE 스트리밍 요청
  Stream<String> streamChat({
    String? imagePath,
    String? message,
  }) async* {
    // FormData 생성
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/chat/stream'),
    );
    
    if (imagePath != null) {
      request.files.add(
        await http.MultipartFile.fromPath('file', imagePath),
      );
    }
    
    if (message != null) {
      request.fields['message'] = message;
    }
    
    // 스트리밍 응답 받기
    var streamedResponse = await request.send();
    
    if (streamedResponse.statusCode != 200) {
      throw Exception('API 오류: ${streamedResponse.statusCode}');
    }
    
    // SSE 파싱
    String buffer = '';
    
    await for (var chunk in streamedResponse.stream.transform(utf8.decoder)) {
      buffer += chunk;
      
      // SSE 라인 분리 (data: ... \n\n)
      var lines = buffer.split('\n\n');
      buffer = lines.last;
      
      for (var i = 0; i < lines.length - 1; i++) {
        if (lines[i].startsWith('data: ')) {
          try {
            // JSON 파싱
            var jsonStr = lines[i].substring(6);
            var jsonData = jsonDecode(jsonStr);
            
            if (jsonData['type'] == 'text') {
              yield jsonData['content'] as String;
            } else if (jsonData['type'] == 'error') {
              throw Exception(jsonData['content']);
            }
          } catch (e) {
            print('JSON 파싱 에러: $e');
          }
        }
      }
    }
  }
}
```

#### 3. UI에서 사용 (StreamBuilder)

```dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final SafetyApiService _apiService = SafetyApiService();
  final TextEditingController _messageController = TextEditingController();
  
  String _response = '';
  bool _isLoading = false;
  String? _imagePath;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('안전 점검 AI')),
      body: Column(
        children: [
          // 이미지 선택 버튼
          ElevatedButton(
            onPressed: _pickImage,
            child: Text(_imagePath == null ? '이미지 선택' : '이미지 변경'),
          ),
          
          // 메시지 입력
          Padding(
            padding: EdgeInsets.all(16),
            child: TextField(
              controller: _messageController,
              decoration: InputDecoration(
                hintText: '질문을 입력하세요...',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
          ),
          
          // 전송 버튼
          ElevatedButton(
            onPressed: _isLoading ? null : _handleSubmit,
            child: Text(_isLoading ? '분석 중...' : '전송'),
          ),
          
          // 응답 표시
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.all(16),
              child: Text(
                _response,
                style: TextStyle(fontSize: 16),
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  Future<void> _pickImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);
    
    if (image != null) {
      setState(() {
        _imagePath = image.path;
      });
    }
  }
  
  Future<void> _handleSubmit() async {
    if (_imagePath == null && _messageController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('이미지 또는 메시지를 입력하세요')),
      );
      return;
    }
    
    setState(() {
      _isLoading = true;
      _response = '';
    });
    
    try {
      await for (var chunk in _apiService.streamChat(
        imagePath: _imagePath,
        message: _messageController.text.isEmpty ? null : _messageController.text,
      )) {
        setState(() {
          _response += chunk;
        });
      }
    } catch (e) {
      setState(() {
        _response = '에러: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
  
  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }
}
```

### Provider 패턴 사용 (권장)

```dart
import 'package:flutter/foundation.dart';

class ChatProvider extends ChangeNotifier {
  final SafetyApiService _apiService = SafetyApiService();
  
  String _response = '';
  bool _isLoading = false;
  String? _error;
  
  String get response => _response;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  Future<void> sendMessage({String? imagePath, String? message}) async {
    _isLoading = true;
    _response = '';
    _error = null;
    notifyListeners();
    
    try {
      await for (var chunk in _apiService.streamChat(
        imagePath: imagePath,
        message: message,
      )) {
        _response += chunk;
        notifyListeners();
      }
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  void clear() {
    _response = '';
    _error = null;
    notifyListeners();
  }
}

// 사용 예시
// Provider 등록 (main.dart)
// ChangeNotifierProvider(create: (_) => ChatProvider())

// 위젯에서 사용
class ChatWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<ChatProvider>(
      builder: (context, chatProvider, child) {
        return Column(
          children: [
            if (chatProvider.isLoading)
              CircularProgressIndicator(),
            
            if (chatProvider.error != null)
              Text('에러: ${chatProvider.error}', style: TextStyle(color: Colors.red)),
            
            Expanded(
              child: SingleChildScrollView(
                child: Text(chatProvider.response),
              ),
            ),
            
            ElevatedButton(
              onPressed: chatProvider.isLoading ? null : () {
                chatProvider.sendMessage(message: '안전보건법 제38조는?');
              },
              child: Text('질문하기'),
            ),
          ],
        );
      },
    );
  }
}
```

---

## 요청/응답 스키마

### 요청 타입별 처리

#### 유형 1: 이미지만 전송

```bash
curl -X POST http://localhost:8000/chat/stream \
  -F "file=@photo.jpg" \
  -H "Accept: text/event-stream"
```

**처리**: 기본 산안법 점검 프롬프트 자동 적용

**응답 예시** (JSON 버퍼링):
```json
data: {"type":"text","content":"비계 점검 결과:\n## 1. 보호구"}
data: {"type":"text","content":" 착용 여부"}
data: {"type":"text","content":"\n- 안전모: 미착용 (×위반)"}
data: {"type":"text","content":"\n\n## 2. 난간대 높이"}
data: {"type":"text","content":"\n- 현황: 85cm\n- 기준:"}
data: {"type":"text","content":" 90cm 이상"}
```

#### 유형 2: 이미지 + 질문

```bash
curl -X POST http://localhost:8000/chat/stream \
  -F "file=@photo.jpg" \
  -F "message=비계의 난간대 높이 기준은?" \
  -H "Accept: text/event-stream"
```

**처리**: 맞춤형 이미지 분석

#### 유형 3: 문서 생성

```bash
curl -X POST http://localhost:8000/chat/stream \
  -F "message=위험성평가 체크리스트를 마크다운으로 만들어줘" \
  -H "Accept: text/event-stream"
```

**문서 생성 키워드**: `작성`, `체크리스트`, `표`, `위험성평가`, `만들어`

#### 유형 4: 일반 질의응답

```bash
curl -X POST http://localhost:8000/chat/stream \
  -F "message=산업안전보건법 제15조의 내용은?" \
  -H "Accept: text/event-stream"
```

### 응답 스키마

#### 성공 응답 (200)

```
data: 응답텍스트청크1
data: 응답텍스트청크2
...
```

#### 에러 응답

**400 - 잘못된 요청**:
```json
{
  "detail": {
    "type": "error",
    "status": "fail",
    "content": "파일 또는 메시지 중 하나는 반드시 제공되어야 합니다.",
    "error_code": "INVALID_INPUT"
  }
}
```

**413 - 파일 크기 초과**:
```json
{
  "detail": {
    "type": "error",
    "status": "fail",
    "content": "파일이 10MB를 초과했습니다.",
    "error_code": "FILE_TOO_LARGE"
  }
}
```

**415 - 지원하지 않는 파일 타입**:
```json
{
  "detail": {
    "type": "error",
    "status": "fail",
    "content": "지원하지 않는 이미지 형식: image/bmp",
    "error_code": "UNSUPPORTED_MEDIA_TYPE"
  }
}
```

**500 - 서버 오류**:
```json
{
  "detail": {
    "type": "error",
    "status": "fail",
    "content": "API 호출 오류 발생",
    "error_code": "API_ERROR"
  }
}
```

---

## 에러 처리

### 에러 코드 맵

| 코드 | HTTP | 설명 | 재시도 |
|------|------|------|--------|
| `INVALID_INPUT` | 400 | 입력 값 검증 실패 | ❌ |
| `FILE_TOO_LARGE` | 413 | 파일 크기 초과 | ❌ |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | 지원하지 않는 형식 | ❌ |
| `API_ERROR` | 500 | Anthropic API 오류 | ✅ |
| `RATE_LIMIT` | 429 | API 요청 한도 초과 | ✅ (재시도 권장) |

### 권장 에러 처리 로직 (Flutter/Dart)

```dart
class SafetyApiService {
  Future<void> chatWithRetry({
    String? imagePath,
    String? message,
    int maxRetries = 3,
  }) async {
    for (int i = 0; i < maxRetries; i++) {
      try {
        await for (var chunk in streamChat(
          imagePath: imagePath,
          message: message,
        )) {
          // 응답 처리
          print(chunk);
        }
        return; // 성공 시 종료
      } catch (e) {
        final errorCode = _extractErrorCode(e);
        
        // 재시도 불가 에러
        if (!['API_ERROR', 'RATE_LIMIT'].contains(errorCode)) {
          rethrow;
        }
        
        // 마지막 시도였다면 에러 던지기
        if (i == maxRetries - 1) {
          rethrow;
        }
        
        // Exponential backoff
        await Future.delayed(Duration(seconds: (i + 1) * 2));
      }
    }
  }
  
  String? _extractErrorCode(dynamic error) {
    final errorStr = error.toString();
    if (errorStr.contains('API_ERROR')) return 'API_ERROR';
    if (errorStr.contains('RATE_LIMIT')) return 'RATE_LIMIT';
    return null;
  }
}
```

---

## 코드 예시

### Flutter 에러 처리 및 재시도

```dart
class SafetyApiService {
  static const int maxRetries = 3;
  static const Duration retryDelay = Duration(seconds: 2);
  
  Stream<String> streamChatWithRetry({
    String? imagePath,
    String? message,
    int retryCount = 0,
  }) async* {
    try {
      await for (var chunk in streamChat(
        imagePath: imagePath,
        message: message,
      )) {
        yield chunk;
      }
    } catch (e) {
      // 재시도 가능한 에러인지 확인
      if (retryCount < maxRetries && _isRetryableError(e)) {
        await Future.delayed(retryDelay * (retryCount + 1));
        
        yield* streamChatWithRetry(
          imagePath: imagePath,
          message: message,
          retryCount: retryCount + 1,
        );
      } else {
        throw e;
      }
    }
  }
  
  bool _isRetryableError(dynamic error) {
    if (error is http.ClientException) return true;
    if (error.toString().contains('API_ERROR')) return true;
    if (error.toString().contains('RATE_LIMIT')) return true;
    return false;
  }
}
```

### Dio 패키지 사용 (고급)

```dart
import 'package:dio/dio.dart';

class SafetyApiClient {
  final Dio _dio;
  
  SafetyApiClient() : _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000',
    connectTimeout: Duration(seconds: 30),
    receiveTimeout: Duration(seconds: 30),
  ));
  
  Stream<String> streamChat({
    String? imagePath,
    String? message,
  }) async* {
    try {
      FormData formData = FormData();
      
      if (imagePath != null) {
        formData.files.add(MapEntry(
          'file',
          await MultipartFile.fromFile(imagePath),
        ));
      }
      
      if (message != null) {
        formData.fields.add(MapEntry('message', message));
      }
      
      // 스트리밍 요청
      final response = await _dio.post(
        '/chat/stream',
        data: formData,
        options: Options(
          responseType: ResponseType.stream,
          headers: {'Accept': 'text/event-stream'},
        ),
      );
      
      // 스트림 파싱
      String buffer = '';
      
      await for (var chunk in response.data.stream.transform(utf8.decoder)) {
        buffer += chunk;
        
        var lines = buffer.split('\n\n');
        buffer = lines.last;
        
        for (var i = 0; i < lines.length - 1; i++) {
          if (lines[i].startsWith('data: ')) {
            var jsonStr = lines[i].substring(6);
            var jsonData = jsonDecode(jsonStr);
            
            if (jsonData['type'] == 'text') {
              yield jsonData['content'] as String;
            }
          }
        }
      }
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }
  
  Exception _handleDioError(DioException e) {
    if (e.response?.statusCode == 400) {
      return Exception('잘못된 요청: ${e.response?.data}');
    } else if (e.response?.statusCode == 413) {
      return Exception('파일 크기가 10MB를 초과했습니다');
    } else if (e.response?.statusCode == 415) {
      return Exception('지원하지 않는 이미지 형식입니다');
    } else {
      return Exception('네트워크 오류: ${e.message}');
    }
  }
}
```

### 완전한 UI 예시 (GetX 패턴)

```dart
// controller.dart
import 'package:get/get.dart';

class ChatController extends GetxController {
  final SafetyApiService _apiService = SafetyApiService();
  
  final response = ''.obs;
  final isLoading = false.obs;
  final error = Rxn<String>();
  final imagePath = Rxn<String>();
  
  Future<void> sendMessage(String? message) async {
    if (imagePath.value == null && (message == null || message.isEmpty)) {
      Get.snackbar('오류', '이미지 또는 메시지를 입력하세요');
      return;
    }
    
    isLoading.value = true;
    response.value = '';
    error.value = null;
    
    try {
      await for (var chunk in _apiService.streamChat(
        imagePath: imagePath.value,
        message: message,
      )) {
        response.value += chunk;
      }
    } catch (e) {
      error.value = e.toString();
    } finally {
      isLoading.value = false;
    }
  }
  
  void clear() {
    response.value = '';
    error.value = null;
    imagePath.value = null;
  }
}

// screen.dart
class ChatScreen extends GetView<ChatController> {
  final TextEditingController _textController = TextEditingController();
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('안전 점검 AI')),
      body: Column(
        children: [
          // 이미지 선택
          Obx(() => controller.imagePath.value != null
            ? Image.file(File(controller.imagePath.value!))
            : ElevatedButton(
                onPressed: _pickImage,
                child: Text('이미지 선택'),
              ),
          ),
          
          // 메시지 입력
          Padding(
            padding: EdgeInsets.all(16),
            child: TextField(
              controller: _textController,
              decoration: InputDecoration(
                hintText: '질문을 입력하세요...',
                border: OutlineInputBorder(),
              ),
            ),
          ),
          
          // 전송 버튼
          Obx(() => ElevatedButton(
            onPressed: controller.isLoading.value
              ? null
              : () => controller.sendMessage(_textController.text),
            child: Text(controller.isLoading.value ? '분석 중...' : '전송'),
          )),
          
          // 응답 표시
          Expanded(
            child: Obx(() {
              if (controller.error.value != null) {
                return Center(
                  child: Text(
                    '에러: ${controller.error.value}',
                    style: TextStyle(color: Colors.red),
                  ),
                );
              }
              
              return SingleChildScrollView(
                padding: EdgeInsets.all(16),
                child: SelectableText(
                  controller.response.value,
                  style: TextStyle(fontSize: 16),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
  
  Future<void> _pickImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);
    
    if (image != null) {
      controller.imagePath.value = image.path;
    }
  }
}
```

### 테스트 코드 (Unit Test)

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';

void main() {
  group('SafetyApiService', () {
    test('streamChat should yield text chunks', () async {
      final apiService = SafetyApiService();
      
      final stream = apiService.streamChat(
        message: '테스트 질문',
      );
      
      final chunks = await stream.toList();
      
      expect(chunks, isNotEmpty);
      expect(chunks.first, isA<String>());
    });
    
    test('should handle errors gracefully', () async {
      final apiService = SafetyApiService();
      
      expect(
        () => apiService.streamChat(imagePath: null, message: null),
        throwsA(isA<Exception>()),
      );
    });
  });
}
```

---

## 성능 및 제한사항

### 요청 제한

| 항목 | 값 |
|------|-----|
| 최대 파일 크기 | 10MB |
| 최대 메시지 길이 | 2000자 |
| 타임아웃 | 30초 |
| Rate Limit | 100 req/min (예정) |

### 응답 크기

| 유형 | 최대 토큰 | 평균 크기 |
|------|----------|----------|
| 이미지 분석 | 800 | 2KB-5KB |
| 문서 생성 | 1500 | 5KB-15KB |
| 질의응답 | 800 | 1KB-3KB |

### 응답 시간

| 유형 | 첫 청크 | 전체 완료 |
|------|--------|----------|
| 이미지 분석 | ~200ms | 1-2초 |
| 문서 생성 | ~300ms | 3-5초 |
| 질의응답 | ~150ms | 1-2초 |

---

## 자주 묻는 질문

### Q1: 스트리밍이 끝나지 않으면?

A: 다음을 확인하세요:
1. 네트워크 연결 상태
2. 브라우저 콘솔의 에러 메시지
3. 30초 타임아웃 설정 확인

### Q2: 이미지가 인식되지 않으면?

A: 다음을 시도하세요:
1. 이미지 형식 확인 (JPEG, PNG, GIF, WebP만 지원)
2. 파일 크기 확인 (10MB 이하)
3. 이미지 품질 확인 (너무 어둡거나 블러된 이미지는 인식 어려움)

### Q3: API 키를 어디서 얻나요?

A: [Anthropic Console](https://console.anthropic.com)에서 생성할 수 있습니다.

### Q4: 로컬 테스트는 어떻게 하나요?

A: README.md의 "빠른 시작" 섹션을 참고하세요.

---

**API 문서 버전**: 2.1.0  
**마지막 업데이트**: 2026-01-10  
**상태**: ✅ 프로덕션 준비 완료

