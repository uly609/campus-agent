# Demo Script

1. Start services with `docker compose up --build -d`.
2. Seed data with `make seed`.
3. Open `http://localhost:5173`.
4. Refresh the post feed.
5. In AI Assistant, ask `图书馆今天几点关门？` and show citations.
6. In Smart Search, search `南门 捡到 校园卡` and show retrieval explanations.
7. In Post Assistant, leave the scene on auto, enter `发布周五晚七点的学院迎新活动，地点在大学生活动中心`, generate an activity draft without an image, edit it, and confirm it.
8. Switch the Post Assistant to lost-and-found, upload the synthetic student-card image, and show VLM-enhanced drafting.
9. Ask chat to remember `记住我喜欢图书馆靠窗座位`; open Memory Management and delete the memory.
10. Run Eval Dashboard.
11. Open Grafana and Prometheus metrics.
