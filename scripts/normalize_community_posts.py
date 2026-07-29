from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings


POST_BODIES = {
    "数字会员闲置转让": "出一个闲置的数字平台会员，有需要的同学可以在评论区问我。虚拟权益交易前请先确认账号和退款规则。",
    "校园大使活动招募": "想问问校内有没有社团或组织愿意参加校园大使活动？有兴趣的可以在评论区交流。",
    "食堂档口关门时间咨询": "想问一下食堂这个档口最晚营业到几点？晚上七点多过去是不是已经关门了？",
    "闲置教材转让": "出线性代数、会计学、世界经济概论、产业经济学等闲置教材，有需要的同学可以评论。",
    "宿舍附近演奏噪声困扰": "凌晨在宿舍附近还能听到乐器声，确实有点影响休息。希望演奏的同学注意一下时间，谢谢。",
    "暑期留校科研采访招募": "想找暑期留校做科研的同学接受一个简短采访，也欢迎大家推荐合适的人选。",
    "乡村振兴比赛队友招募": "乡村振兴相关比赛招队友，有兴趣一起准备的同学可以在评论区聊聊。",
    "图书馆还书服务咨询": "请问学校图书馆现在可以办理还书吗？最近去过的同学麻烦说一下。",
    "教材收书交流群": "想收一些教材，也欢迎有闲置书的同学一起交流书况和价格。",
    "图书馆键盘噪音困扰": "图书馆安静区域的机械键盘声音有点明显，会影响周围同学学习，大家使用设备时能不能稍微注意一下？",
    "教学楼遗失物品询问": "请问有没有同学在文科楼、图书馆四楼或附近教学楼捡到遗失物品？有线索麻烦评论告诉我。",
    "学校游泳馆优惠预约咨询": "想问一下学校游泳馆对本校学生有没有优惠，需要提前预约吗？去过的同学求分享。",
    "写真馆求推荐": "求推荐写真馆，想了解一下价格、成片效果和服务体验，有拍过的同学可以说说。",
    "异地购买物品求助": "想找上海、湖南、江苏或广东的同学帮忙购买一件需要拆封挑选的物品，有经验的同学可以交流一下。",
    "校园附近理发店推荐": "学校附近有没有适合做拉直、柔顺的理发店？想听听大家真实的消费体验。",
    "图书馆开放与选座系统咨询": "请问学校图书馆现在开放吗？选座系统是不是还在维护？知道的同学麻烦说一下。",
    "关于校园人际关系的随笔": "随着年龄、阅历和学历的增长，我越来越觉得能深交、真诚的人变少了，找到合适的另一半好像比考研还难。大家也会有这种感觉吗？",
    "线下游戏体验问卷招募": "兄弟们帮忙填个问卷！杭州线下《代号：FH》体验活动招募，玩过非对称竞技游戏或 MOBA 手游的同学都可以来了解一下。",
}


def normalize_posts(rows: list[dict[str, Any]]) -> int:
    updated = 0
    for row in rows:
        body = POST_BODIES.get(row.get("title"))
        if body is None or row.get("author_alias") != "匿名外部社区":
            continue
        row["body"] = body
        row["author_alias"] = "匿名同学"
        tags = [
            tag
            for tag in row.get("tags", [])
            if tag not in {"哆啦校园", "外部社区快照", "非官方", "安全提醒"}
        ]
        row["tags"] = [*tags, "社区转帖"]
        updated += 1
    return updated


def main() -> None:
    posts_path = Path(get_settings().data_dir) / "runtime_posts.json"
    rows = json.loads(posts_path.read_text(encoding="utf-8"))
    updated = normalize_posts(rows)
    posts_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"normalized {updated} community posts")


if __name__ == "__main__":
    main()
