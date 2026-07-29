---
name: campus-notice
description: 查询项目内置的演示校园通知。用于展示通知查询流程，不代表浙江工商大学当前正式通知。
---

# Campus Notice

Use this skill when the user asks about recent campus announcements, scholarship application notices, semester opening reminders, sports meeting notices, teaching affairs notices, safety notices, or library/service announcements.

## Inputs

The caller may provide any of these optional filters:

- `keyword` or `query`: keyword or original user query, such as `奖学金`, `开学`, `运动会`
- `category`: notice category, such as `奖学金`, `教务`, `活动`, `安全`, `服务`
- `audience`: target audience, such as `本科生`, `全体学生`, `教师`
- `department`: publishing department, such as `学生处`, `教务处`, `体育部`
- `priority`: `high`, `medium`, or `low`
- `date_from` / `date_to`: publication date range in `YYYY-MM-DD`
- `limit`: maximum number of notices to return

## Output

Return matching notices with title, category, publish date, deadline, audience, department, summary, priority, tags, and URL. If no notice matches, say that no accurate campus notice was found for the provided filters.

## Execution

This skill obtains notice data from its bundled reference files:

- `references/notices.json`: notice index and metadata
- `references/notice-*.md`: full notice content

The reference files currently contain mock notice data for development and demos. Read and filter that local data directly; do not call a remote URL to get notices.
