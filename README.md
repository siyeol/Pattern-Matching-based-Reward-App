# Cash Hunter: 수익형 광고 어플리케이션

이 서비스를 사용하여 사용자는 유효한 광고를 찾을 수 있으며, 광고주는 광고 유효성을 검사하여 광고 효과를 높일 수 있습니다.
![image](https://user-images.githubusercontent.com/33966473/227834546-e4abe6cc-322b-44a0-9b9b-62cd6a3e2e54.png)


## 기술 스택

- Flask: 웹 서버 구현을 위한 Python 프레임워크
- Kafka: 분산 스트리밍 플랫폼으로, 메시지 브로커 역할을 수행하여 메시지 큐잉을 제공합니다.
- MySQL: 관계형 데이터베이스로, 사용자 포인트 업데이트와 기록을 위해 사용됩니다.
- MongoDB: NoSQL 데이터베이스로, 광고 유효성 검사 결과를 저장하기 위해 사용됩니다.
- Elasticsearch: 검색 및 분석 엔진으로, 시스템 메트릭 데이터를 수집하여 저장하는 데 사용됩니다.
- OpenCV: 영상처리 라이브러리로, 광고 사진과 사용자가 촬영한 이미지를 비교하는 데 사용됩니다.
- Airflow: 워크플로우 파이프라인으로, 데이터 처리 과정을 자동화하고 스케쥴링하기 위해 사용됩니다.

## Workflow

1. 사용자는 Cash Hunter 모바일 앱을 사용하여 광고 사진을 촬영합니다.
2. 촬영된 이미지는 바이트 형태로 Flask 서버로 전송됩니다.
3. Flask 서버에서는 OpenCV 라이브러리를 사용하여 광고 사진과 사용자가 촬영한 이미지를 비교합니다. SIFT 알고리즘을 사용하여 두 이미지의 특징점을 찾고, FLANN 알고리즘을 사용하여 특징점 간의 매칭을 수행합니다.
4. 매칭된 특징점의 비율이 일정 수준 이상이면 Kafka Producer를 사용하여 광고가 유효하다는 메시지를 전송합니다. 그렇지 않으면 광고가 유효하지 않다는 메시지를 전송합니다.
5. Kafka Consumer는 유효한 광고 메시지를 수신하면 MongoDB 데이터베이스에 저장합니다.
6. MySQL 데이터베이스는 사용자의 포인트를 업데이트하고, 사용자의 포인트 기록을 기록합니다.
7. Elasticsearch는 Kafka Consumer에서 수신한 시스템 메트릭 데이터를 수집하여 저장합니다.
8. Airflow를 통해 매주 어플리케이션 사용 패턴을 분석하고 결과를 MongoDB에 저장합니다.

## What makes this a Data Engineering Project?

- 데이터 분석 : MongoDB의 데이터를 분석하기 위한 Airflow 파이프라인을 구현하였습니다. 주간 광고별 성공률 계산, 위치별 평균 성공률 계산, 일별 매치 수 계산을 분석해 MongoDB에 저장해 줍니다.
- 데이터 추출 : Psutil을 통해 수집한 system-metric-log를 Kafka를 통해 Elasticsearch에 저장하고, Kibana를 통해 시각화 하여 서비스 상태 모니터링을 가능케 하였습니다.
- 데이터 관리 : RDBMS와 NoSQL의 용례를 분석하고 MySQL, MongoDB, ElasticSearch를 적용해 각각의 장점과 용도에 맞게 활용했습니다.

## 시스템 구조
![image](https://user-images.githubusercontent.com/33966473/227839292-7f47b2de-d4ba-40c5-a99e-bfc74dbfbe03.png)

