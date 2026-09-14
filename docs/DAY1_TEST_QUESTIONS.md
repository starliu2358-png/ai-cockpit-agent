# Vehicle Book Day 1 Test Questions

> 本文件定义后续 RAG 评估问题，不在 Day 1 实现自动评测。所有车辆与参数均为虚构测试数据。

## ASTER_X1 V1 — MAX — Software 1.0

1. LCC 是什么？
2. 30 km/h 可以开启 LCC 吗？
3. 80 km/h 可以开启 LCC 吗？
4. 我的车支持 HPA 吗？
5. MAX 配置支持座椅通风吗？
6. 电池容量是多少？
7. 最大直流快充功率是多少？

Expected facts:

- LCC activation range: 60–120 km/h
- HPA: unsupported
- Seat ventilation: MAX only
- Battery: 75 kWh
- Maximum DC fast charging: 150 kW

## ASTER_X1 V2 — MAX — Software 2.0

8. 30 km/h 可以开启 LCC 吗？
9. 我的车支持 HPA 吗？
10. 最大直流快充功率是多少？

Expected facts:

- LCC activation range: 0–130 km/h
- HPA: supported
- Seat ventilation: MAX only
- Battery: 75 kWh
- Maximum DC fast charging: 180 kW

## ASTER_X2 V1 — MAX — Software 1.0

11. PRO 配置支持座椅通风吗？
12. 电池容量是多少？
13. HPA 支持吗？

Expected facts:

- LCC activation range: 0–130 km/h
- HPA: supported
- Seat ventilation: PRO and MAX
- Battery: 90 kWh
- Maximum DC fast charging: 240 kW

## Fallback

14. 我的车支持飞行模式吗？
15. 车辆能不能自动去火星？

Expected behavior:

- State that the synthetic knowledge base has no supporting evidence.
- Do not invent a feature, procedure, or source.
- Do not retrieve evidence from another model or software version.
