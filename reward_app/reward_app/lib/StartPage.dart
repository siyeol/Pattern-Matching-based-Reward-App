import 'dart:async';

import 'package:flutter/material.dart';
import 'Option.dart';

class FirstScreenWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Container( //컨테이너로 감싼다.
        decoration: BoxDecoration( //decoration 을 준다.
            image: DecorationImage(
                image: AssetImage("pagecover.png"),
                fit: BoxFit.cover)),
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