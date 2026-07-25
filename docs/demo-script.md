# Demo Script

1. Start services with `docker compose up --build -d`.
2. Seed data with `make seed`.
3. Open `http://localhost:5173`.
4. Refresh the post feed.
5. In AI Assistant, ask `图书馆今天几点关门？`, then follow with `那周末呢？`; show the continuous transcript, topic resolution, and deduplicated citation.
6. Ask `学校明年会不会建地铁站？` to demonstrate evidence-insufficient refusal.
7. In Smart Search, search `课表在哪里看`, open the first result, and show its full official source detail.
8. In Post Assistant, leave the scene on auto, enter `发布周五晚七点的学院迎新活动，地点在大学生活动中心`, generate an activity draft without an image, edit it, and confirm it.
9. Switch the Post Assistant to second-hand and generate a calculator listing to show that drafting is not limited to lost and found.
10. Switch to lost-and-found, upload the synthetic student-card image, and show VLM-enhanced drafting.
11. Ask chat to remember `记住我喜欢图书馆靠窗座位`; open Memory Management and delete the memory.
12. Run Eval Dashboard.
13. Open Grafana and Prometheus metrics.
