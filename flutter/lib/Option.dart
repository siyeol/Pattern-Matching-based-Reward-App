import 'package:flutter/material.dart';
import 'main.dart';

class OptionWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Container( //컨테이너로 감싼다.
        decoration: BoxDecoration( //decoration 을 준다.
            image: DecorationImage(
                image: AssetImage("option.png"),
                fit: BoxFit.cover)
        ),
        child: Scaffold(
          body: LayoutBuilder(
            builder: (context, constrains) => TextButton(
              style: TextButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  fixedSize: Size(
                      constrains.maxHeight,
                      constrains.maxHeight
                  ),
                  splashFactory: NoSplash.splashFactory,
                  minimumSize: Size.infinite
              ),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => MyHomePage(title: 'Reward App')),
                );
              },
            ),
          ),
          appBar: AppBar(
            backgroundColor: const Color(0xFF51C8BE),
            elevation: 0,
          ),
          backgroundColor: Colors.transparent, //스캐폴드에 백그라운드를 투명하게 한다.
        ),
      ),
    );
  }

}