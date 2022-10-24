import 'package:flutter/material.dart';
import 'package:reward_app/Option.dart';
import 'package:dio/dio.dart';

class MyPageWidget extends StatelessWidget {

  void _fetchMyData() async {
    // Get base file name
    try {
      Dio dio = new Dio();

      await dio.post("http://172.30.1.54:5000/mypage", data: {"uid" : "testUser"})
          .then((response) => print(response))
          .catchError((error) => print(error));

    } catch (e) {
      print("Exception Caught: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Container( //컨테이너로 감싼다.
        decoration: BoxDecoration( //decoration 을 준다.
            image: DecorationImage(
                image: AssetImage("mypage.png"),
                fit: BoxFit.cover)),
        child: Scaffold(
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            leading: new IconButton(
              icon: new Icon(Icons.refresh),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => OptionWidget()),
                );
              },
            ),
          ),
          backgroundColor: Colors.transparent, //스캐폴드에 백그라운드를 투명하게 한다.
        ),
      ),
    );
  }


}