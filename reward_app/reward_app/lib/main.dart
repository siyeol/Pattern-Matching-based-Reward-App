import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'package:path/path.dart';
import 'package:dio/dio.dart';
import 'package:reward_app/StartPage.dart';
import 'package:reward_app/MyPage.dart';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Reward App',
      theme: ThemeData(

        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: const Color(0xFF51C8BE),
      ),
      // home: MyHomePage(title: 'Reward App'), //원래 이거
      home: FirstScreenWidget(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  MyHomePage({Key key, this.title}) : super(key: key);

  final String title;

  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  File _image;
  final GlobalKey<ScaffoldState> _scaffoldstate =
  new GlobalKey<ScaffoldState>();

  Future getImage() async {
    var image = await ImagePicker.pickImage(source: ImageSource.camera);
    _uploadFile(image);

    setState(() {
      _image = image;
    });
  }

  // Methode for file upload
  void _uploadFile(filePath) async {
    // Get base file name
    String fileName = basename(filePath.path);
    print("File base name: $fileName");

    try {
      FormData data = FormData.fromMap({
        "file": await MultipartFile.fromFile(
          filePath.path,
          filename: fileName,
          // contentType: MediaType('type', 'subtype'), //important
        ),
      });
      print(data);

      Dio dio = new Dio();

      await dio.post("http://172.30.1.54:5000/", data: data)
          .then((response) => print(response))
          .catchError((error) => print(error));

    } catch (e) {
      print("Exception Caught: $e");
    }
  }


  Future updateDB() async {
    _updateDB();
  }

  void _updateDB() async {
    // Get base file name
    try {
      FormData data = FormData.fromMap({
        "uid": 10002
      });

      Dio dio = new Dio();

      await dio.post("http://172.30.1.54:5000/update", data: data)
          .then((response) => print(response))
          .catchError((error) => print(error));
    } catch (e) {
      print("Exception Caught: $e");
    }
  }


  @override
  Widget build(BuildContext context) {

    return Scaffold(
      key: _scaffoldstate,
      backgroundColor: const Color(0xFF51C8BE),
      appBar: AppBar(
        backgroundColor: const Color(0xFF51C8BE),
        elevation: 0,
          actions: <Widget>[
            new IconButton(
              icon: new Icon(Icons.home),
              onPressed: () {
                Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => MyPageWidget()),
                );
              },
            ),
          ],
      ),
      // backgroundColor: const Color(0xFF51C8BE),
      body: Center(
        // Center is a layout widget. It takes a single child and positions it
        // in the middle of the parent.
        child: _image == null ? Text('사진을 찍어주세요', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)) : Image.file(_image),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: getImage,
        child: Icon(Icons.camera_alt),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ), // This trailing comma makes auto-formatting nicer for build methods.

      // floatingActionButtonLocation: FloatingActionButtonLocation.centerTop,
    );
  }
}