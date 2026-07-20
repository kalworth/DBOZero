from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from .glossary import CURATED_TRANSLATIONS
except ImportError:  # Keep direct script execution working.
    from glossary import CURATED_TRANSLATIONS


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "new_translations.tsv"
TRANSLATIONS_PATH = ROOT / "data" / "translations.tsv"
LEGACY_TOOLS = ROOT / "legacy" / "tools"
# Legacy dictionaries remain a fallback dependency, but must not shadow v3
# entrypoints such as the repository-level build_output.py.
sys.path.append(str(LEGACY_TOOLS))

from auto_translate_new_source import PHRASE_MAP, WORD_MAP, translate_name  # noqa: E402


INTERNAL_IDENTIFIER_RE = re.compile(
    r"^(?:"
    r"[A-Z]{2,}_[A-Z0-9_]+|"
    r"HEN Buff \d+ Lv\d+|"
    r"Buff SK \d+|"
    r"(?:MOB|Mob) Makai\d+(?:Frog)?|"
    r"(?:FreezatoGolden|\d+FreezaSkill)|"
    r"\d+TOWA Makai|"
    r"TIAL SS4Daima"
    r")$"
)


EXACT_MAP = {
    "Account Creation Successful": "账号创建成功",
    "Authentication Failure": "验证失败",
    "Normal": "普通",
    "Social": "社交",
    "Aggro List": "仇恨列表",
    "Your Aggro.": "你的仇恨。",
    "Party's Aggro.": "队伍仇恨。",
    "Pet's Aggro.": "宠物仇恨。",
    "Motion posture": "动作姿势",
    "You can't fly right now.": "你现在无法飞行。",
    "You can't fly during a fight.": "战斗中无法飞行。",
    "Air effect": "飞行特效",
    "Air pose": "飞行姿势",
    "Auction House": "拍卖行",
    "Cannot open Mail or Auction House while in combat.": "无法在战斗中打开邮件或拍卖行。",
    "That type has already been equipped.": "该类型已经装备。",
    "You are already on this Channel": "你已经在该频道。",
    "Remaining amount of recovery: %s": "剩余恢复量：%s",
    "Must wait %s seconds after recovery": "恢复后必须等待 %s 秒",
    "Female": "女性",
    "Male": "男性",
    "No Gender": "无性别",
    "Axe": "斧",
    "Date": "日期",
    "Backpack": "背包",
    "Tail": "尾巴",
    "Remote Sales": "远程出售",
    "Mail and Auction House will close automatically when you enter combat.": "进入战斗时，邮件和拍卖行会自动关闭。",
    "Bag Slot": "背包栏位",
    "Inventory": "背包",
    "Basic Position": "基本姿势",
    "Armor Properties:": "防具属性：",
    "Weapon Properties:": "武器属性：",
    "Attributes:": "属性：",
    "On Target": "目标",
    "Insufficient Zeni.": "索尼不足。",
    "Can't attack.": "无法攻击。",
    "Bazooka": "火箭筒",
    "%d%% Bonus EXP": "经验值加成 %d%%",
    "NetStore Available": "可使用商城仓库",
    "%d%% Bonus Vehicle speed": "载具速度加成 %d%%",
    "%d%% Bonus Zeni": "索尼加成 %d%%",
    "Bonus": "加成",
    "This is your new Home Teleport area!": "这里已设为你的新回城传送区域！",
    "Bleeding Def.": "出血防御",
    "Block is on cooldown": "格挡正在冷却",
    "Scan jammed": "扫描受阻",
    "Dojo Finalists": "道场决赛选手",
    "Class": "职业",
    "Guild": "公会",
    "Level": "等级",
    "Name": "名称",
    "Battle Points": "战斗点数",
    "Battle Rank": "战斗排名",
    "%dW %dL %dD": "%d胜 %d负 %d平",
    "RO16": "16强",
    "RO16 standby": "16强待命",
    "RO32": "32强",
    "RO32 standby": "32强待命",
    "RO8": "8强",
    "RO8 standby": "8强待命",
    "Awards": "奖励",
    "Finals": "决赛",
    "Semi-finals": "半决赛",
    "Semi-final standby": "半决赛待命",
    "Alive": "存活",
    "Battle Royale": "大乱斗",
    "Qualifiers": "预选赛",
    "Party": "队伍",
    "Solo": "单人",
    "Total": "总计",
    "Cancel": "取消",
    "Register": "报名",
    "Registration failed.": "报名失败。",
    "yes": "是",
    "Yes": "是",
    "ALL": "全部",
    "All": "全部",
    "Time left": "剩余时间",
    "Time Left": "剩余时间",
    "N/A": "N/A",
    "Cooldown : %s": "冷却：%s",
    "Battle Ranked": "战斗排名",
    "Ranked Battle": "排位战斗",
    "AP is consumed only during accelerated flying.\\nIt regenerates while you fly slowly or while on ground.": "AP只会在加速飞行时消耗。\\n慢速飞行或在地面时会恢复。",
    "Popo's Chest box contains an exp. scroll.": "波波宝箱中含有经验卷轴。",
    "You're about to change channel.": "你即将切换频道。",
    "If %s less than %d%% recover %d%% ": "当 %s 低于 %d%% 时恢复 %d%% ",
    "Damage %.0f%%": "伤害 %.0f%%",
    " Attack Attribute: %.0f%%": " 攻击属性：%.0f%%",
    "Defense %.0f%%": "防御 %.0f%%",
    " Defense Attribute: %.0f%%": " 防御属性：%.0f%%",
    "%s CLEARED CC Battle Dungeon 40 Floor": "%s 已通关 CC战斗副本40层",
    "%s CLEARED CC Battle Dungeon 200 Floor": "%s 已通关 CC战斗副本200层",
    "CC Battle Dungeon 200 Floor WAS CLEARED": "CC战斗副本200层已通关",
    "Qualifier standby": "预选赛待命",
    "K.O": "K.O",
    "Please Wait I'm Busy": "请稍等，我正忙",
    "%d seconds to KO": "%d 秒后 K.O",
    "%d seconds to ring out": "%d 秒后出界",
    "Mudosa Village %d": "武道寺村 %d",
    "TP INFO: 200,000 Zeni Fee": "传送信息：费用 200,000 索尼",
    "Join Solo": "参加单人赛",
    "Join Team": "参加团队赛",
    "Receipt": "收据",
    "Tournament": "锦标赛",
    "Party Leader Apply": "队长申请",
    "Left Party": "离开队伍",
    "Tenkaichi Budokai": "天下第一武道会",
    "Budokai is closed!": "武道会已关闭！",
    "Best Dojo": "最佳道场",
    "Tournament Qualifiers": "锦标赛预选赛",
    "Budokai is open!": "武道会已开放！",
    "Register now!": "立即报名！",
    "Undecided": "未决定",
    "Application Period": "申请期间",
    "Sign Up": "报名",
    "State Info": "状态信息",
    "1st/2nd": "第1/第2名",
    "No Winners": "无获胜者",
    "Team Sign Up": "团队报名",
    "Team State Info": "团队状态信息",
    "Team 1st/2nd": "团队第1/第2名",
    "No Winning Party": "无获胜队伍",
    "You have not signed up.": "你尚未报名。",
    "Loading Data...": "正在读取数据...",
    "RO16 contestant": "16强参赛者",
    "RO16 finalist": "16强晋级者",
    "RO32 contestant": "32强参赛者",
    "RO32 finalist": "32强晋级者",
    "RO8 contestant": "8强参赛者",
    "RO8 finalist": "8强晋级者",
    "Finalist": "决赛选手",
    "Winner": "获胜者",
    "Qualifier": "预选赛选手",
    "Contestant": "参赛者",
    "Qualifier finalist": "预选赛晋级者",
    "Semi-finalist": "半决赛选手",
    "Runner-up": "亚军",
    "All battles have ended.": "所有战斗已结束。",
    "Upcoming: Final": "即将开始：决赛",
    "Stay & Be Rewarded": "留下即可获得奖励",
    "Qualifier": "预选赛",
    "Tournament starts soon": "锦标赛即将开始",
    "Registration close soon": "报名即将关闭",
    "Enter the Tournament": "进入锦标赛",
    "Please Join": "请加入",
    "Budokai Announcement": "武道会公告",
    "Semi Final On-Going": "半决赛进行中",
    "Semi-final": "半决赛",
    "The Tournament is about to Start!": "锦标赛即将开始！",
    "Registration period": "报名期间",
    "Final": "决赛",
    "Qualification": "资格赛",
    "Preliminary": "预赛",
    "Application": "申请",
    "PvP Arena (FFA)": "PvP竞技场（FFA）",
    "Player Kills": "玩家击杀数",
    "No registered players yet.": "尚无已报名玩家。",
    "Close": "关闭",
    "Team": "团队",
    "Leader": "队长",
    "Match Info": "比赛信息",
    "Level %d": "等级 %d",
    "Name : ": "名称：",
    "Mudosa": "武道寺",
    "Ticket": "门票",
    "%d day": "%d 天",
    "%d hour": "%d 小时",
    "%d minute": "%d 分钟",
    "%d second": "%d 秒",
    "Group A": "A组",
    "Group B": "B组",
    "Qualifiers will continue.": "预选赛将继续。",
    "Senior": "成人组",
    "Kid": "儿童组",
    "%s Buff Activated": "%s 增益已激活",
    "Can't Remove Buff": "无法移除增益",
    "Can't Remove": "无法移除",
    "Buff Restriction": "增益限制",
    "Burn Def.": "灼烧防御",
    "Ride Bus?": "乘坐巴士？",
    "Paid %u": "已支付 %u",
    "Can't use Shenron's altar": "无法使用神龙祭坛",
    "Too many windows open": "打开的窗口过多",
    "Cash": "现金",
    "Cash Items": "现金道具",
    "Warning Messages": "警告消息",
    "Floor : %d": "楼层：%d",
    "Enter": "进入",
    "Ready": "准备",
    "Wait": "等待",
    "Challenge Settings": "挑战设置",
    "Setup": "设置",
    "Complete": "完成",
    "Floor %d can be entered": "可进入第 %d 层",
    "Use the menu on the left to leave party.": "使用左侧菜单离开队伍。",
    "Choose one.": "选择一项。",
    "CCBD Awards": "CCBD奖励",
    "Dungeon battle success": "副本战斗成功",
    "Floor %d complete": "第 %d 层完成",
    "Congrats! Dungeon Complete": "恭喜！副本完成",
    "Challenge": "挑战",
    "Move": "移动",
    "Choosing...": "选择中...",
    "Selection": "选择",
    "LP/EP recovery disabled": "LP/EP恢复已禁用",
    "EXP gains disabled": "经验获取已禁用",
    "Consumables disabled": "消耗品已禁用",
    "Please Wait.": "请稍等。",
    "Element Slot": "属性栏位",
    "Insert gloves or jacket here.": "请在此放入手套或上衣。",
    "Select an element before continuing.": "继续前请选择属性。",
    "VIP Remote Services": "VIP远程服务",
    "Can't join Budokai.": "无法参加武道会。",
    "Budokai Receptionist": "武道会接待员",
    "Tenkaichi": "天下第一",
    "Budokai Menu": "武道会菜单",
    "Budokai Disabled": "武道会已禁用",
    "Budokai Finals": "武道会决赛",
    "Budokai Qualifiers": "武道会预选赛",
    "Budokai Match": "武道会比赛",
    "Budokai Preliminaries": "武道会预赛",
    "Budokai is in progress.": "武道会进行中。",
    "Budokai isn't open.": "武道会未开放。",
    "Already joined Budokai.": "已经加入武道会。",
    "Unable while in Budokai.": "武道会期间无法进行。",
    "Unable to join Budokai during Scramble event.": "争夺战活动期间无法参加武道会。",
    "Can't Sign": "无法签名",
    "2-8 Characters": "2-8个字符",
    "Need Master Class": "需要转职职业",
    "You are a kid!": "你是儿童！",
    "You are an adult!": "你是成人！",
    "Can't whisper yourself.": "不能密语自己。",
    "Command: %s": "命令：%s",
    "Down": "下",
    "Unlock": "解锁",
    "Not in a Party": "不在队伍中",
    "To whisper enter [/w ID].": "要发送密语请输入 [/w ID]。",
    "%s isn't Online": "%s 不在线",
    "No User to Reply": "没有可回复的用户",
    "end": "结束",
    "LFP": "寻找队伍",
    "Guild Master": "公会会长",
    "%s: ": "%s：",
    "Chat mode": "聊天模式",
    "Chat disconnected.": "聊天已断开。",
    "Chat connected.": "聊天已连接。",
    "Chat Server Notification": "聊天服务器通知",
    "Don't Spam": "不要刷屏",
    "Don't Spam the Shout": "不要刷世界喊话",
    "Chatting Too Fast": "聊天过快",
    "[%s] %s: %s": "[%s] %s：%s",
    "[%s] From '%s': %s": "[%s] 来自 '%s'：%s",
    "[%s] To '%s': %s": "[%s] 发给 '%s'：%s",
}
EXACT_MAP.update(CURATED_TRANSLATIONS)


def load_existing_translation_map(path: Path = TRANSLATIONS_PATH) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not path.exists():
        return mapping
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            source = (row.get("source_text") or "").strip()
            target = (row.get("zh_cn") or "").strip()
            if not source or not target:
                continue
            mapping.setdefault(source, target)
    return mapping


WORD_MAP.update(
    {
        "Account": "账号",
        "Access": "访问",
        "Creation": "创建",
        "Successful": "成功",
        "Authentication": "验证",
        "Failure": "失败",
        "Failed": "失败",
        "Connect": "连接",
        "Server": "服务器",
        "Please": "请",
        "Try": "尝试",
        "Again": "再次",
        "Minutes": "分钟",
        "Aggro": "仇恨",
        "List": "列表",
        "Posture": "姿势",
        "Registration": "报名",
        "Finalists": "决赛选手",
        "Qualifiers": "预选赛",
        "Awards": "奖励",
        "Standby": "待命",
        "Def": "防御",
        "Properties": "属性",
        "Attribute": "属性",
        "Attributes": "属性",
        "Inventory": "背包",
        "Bag": "背包",
        "Slot": "栏位",
        "Sales": "出售",
        "Remote": "远程",
        "Channel": "频道",
        "Female": "女性",
        "Male": "男性",
        "Gender": "性别",
        "Home": "回城",
        "Teleport": "传送",
        "Location": "位置",
        "Area": "区域",
        "Jammed": "受阻",
        "Scan": "扫描",
        "Cooldown": "冷却",
        "Remaining": "剩余",
        "Amount": "数量",
        "Recovery": "恢复",
        "Seconds": "秒",
        "Equipped": "装备",
        "Type": "类型",
        "Fight": "战斗",
        "Fly": "飞行",
        "Flying": "飞行",
        "Effect": "特效",
        "Pose": "姿势",
        "Available": "可用",
        "Vehicle": "载具",
        "Speed": "速度",
        "Bonus": "加成",
        "Bleeding": "出血",
        "Budokai": "武道会",
        "Dojo": "道场",
        "Finals": "决赛",
        "Semi": "半",
        "Alive": "存活",
        "Enemy": "敌人",
        "Record": "记录",
        "Rank": "排名",
        "Points": "点数",
        "a": "",
        "A": "A",
        "able": "可以",
        "about": "即将",
        "above": "以上",
        "access": "访问",
        "acquired": "已获得",
        "all": "全部",
        "allowed": "允许",
        "already": "已经",
        "amount": "数量",
        "an": "",
        "any": "任何",
        "applied": "应用",
        "are": "是",
        "Ask": "询问",
        "automatically": "自动",
        "be": "被",
        "because": "因为",
        "been": "已",
        "before": "之前",
        "begun": "开始",
        "being": "正在",
        "blocked": "被阻止",
        "Board": "公告板",
        "Balls": "球",
        "Blacklisted": "黑名单",
        "button": "按钮",
        "but": "但",
        "can": "可以",
        "cast": "施放",
        "chance": "几率",
        "change": "更改",
        "changed": "已更改",
        "Character": "角色",
        "character": "角色",
        "Characters": "角色",
        "characters": "角色",
        "checked": "检查中",
        "city": "城市",
        "Classes": "职业",
        "cleared": "清除",
        "client": "客户端",
        "close": "关闭",
        "color": "颜色",
        "configured": "配置",
        "Confirmation": "确认",
        "conditions": "条件",
        "consumed": "消耗",
        "contains": "包含",
        "Could": "无法",
        "Couldn't": "无法",
        "couldn't": "无法",
        "crafting": "制作",
        "Crafting": "制作",
        "cry": "哭泣",
        "day": "天",
        "Days": "天",
        "decide": "决定",
        "Description": "说明",
        "Dialog": "频道",
        "dice": "骰子",
        "Dice": "骰子",
        "different": "不同",
        "disable": "禁用",
        "Disassemble": "分解",
        "Disconnecting": "正在断开",
        "disconnected": "断开连接",
        "Divide": "分配",
        "down": "下",
        "downgraded": "降级",
        "durability": "耐久度",
        "each": "每",
        "effects": "效果",
        "element": "属性",
        "Elimination": "淘汰",
        "empty": "空",
        "Eng": "气功",
        "ensure": "确认",
        "enter": "进入",
        "entered": "已进入",
        "entrance": "入口",
        "EV": "活动",
        "exceeded": "超过",
        "exist": "存在",
        "exists": "存在",
        "Expert": "专家",
        "Extend": "延长",
        "fails": "失败",
        "far": "远",
        "Fearland": "恐惧之地",
        "final": "决赛",
        "First": "第一",
        "first": "第一",
        "following": "以下",
        "found": "找到",
        "free": "免费",
        "Free": "自由",
        "frm": "文件",
        "function": "功能",
        "Gameguard": "安全程序",
        "GMTool": "GM工具",
        "Good": "好",
        "Guild": "公会",
        "guild": "公会",
        "gui": "界面",
        "hasn't": "尚未",
        "higher": "更高",
        "Hide": "隐藏",
        "hour": "小时",
        "Hours": "小时",
        "I": "我",
        "increase": "增加",
        "Increase": "增加",
        "Increases": "增加",
        "Information": "信息",
        "information": "信息",
        "inserted": "已放入",
        "invite": "邀请",
        "joined": "已加入",
        "kick": "踢出",
        "last": "上一条",
        "learn": "学习",
        "Learn": "学习",
        "level": "等级",
        "Level": "等级",
        "like": "像",
        "Limit": "限制",
        "limit": "限制",
        "locked": "锁定",
        "longer": "更久",
        "lose": "失去",
        "Machines": "机器",
        "Mascot": "吉祥物",
        "max": "最大",
        "Max": "最大",
        "maximum": "最大",
        "meet": "满足",
        "Merchant": "商人",
        "Mine": "矿山",
        "missing": "缺少",
        "Mix": "混合",
        "more": "更多",
        "More": "更多",
        "movie": "影片",
        "Name": "名称",
        "name": "名称",
        "needed": "需要",
        "nProtect": "安全程序",
        "Nr": "第",
        "number": "数量",
        "obtain": "获得",
        "occurred": "发生",
        "Offline": "离线",
        "one": "一个",
        "other": "其他",
        "over": "结束",
        "owner": "拥有者",
        "panel": "面板",
        "password": "密码",
        "permission": "权限",
        "Phy": "物理",
        "Place": "放置",
        "play": "游玩",
        "Price": "价格",
        "problem": "问题",
        "Quest": "任务",
        "quest": "任务",
        "Quests": "任务",
        "Rate": "概率",
        "re": "重新",
        "reached": "已达到",
        "reaching": "到达",
        "Rebuild": "重建",
        "recommendations": "推荐",
        "Reduces": "减少",
        "Reduced": "减少",
        "removed": "移除",
        "Removal": "移除",
        "Rename": "改名",
        "renaming": "改名",
        "Renew": "续期",
        "reply": "回复",
        "Ribbon": "缎带军",
        "run": "运行",
        "sacrifice": "辅助",
        "schedule": "日程",
        "Scramble": "争夺战",
        "scramble": "争夺战",
        "Seal": "封印",
        "seal": "封印",
        "Second": "第二",
        "Select": "选择",
        "select": "选择",
        "selection": "选择",
        "sell": "出售",
        "share": "分享",
        "Share": "分享",
        "Show": "显示",
        "skipped": "跳过",
        "skip": "跳过",
        "Slots": "栏位",
        "sold": "已出售",
        "spawn": "复活",
        "starts": "开始",
        "Store": "商店",
        "Style": "风格",
        "Sub": "子",
        "summon": "召唤",
        "Summon": "召唤",
        "summoned": "已召唤",
        "system": "系统",
        "System": "系统",
        "takes": "需要",
        "tap": "点击",
        "Team": "团队",
        "that": "该",
        "That": "那",
        "them": "它们",
        "There": "有",
        "too": "太",
        "Too": "太",
        "Tournament": "锦标赛",
        "Tenkaichi": "天下第一",
        "trade": "交易",
        "Trade": "交易",
        "transfer": "转移",
        "Trigger": "触发",
        "Tutorial": "教程",
        "Underground": "地下",
        "Unlocks": "解锁",
        "until": "直到",
        "upgraded": "已升级",
        "View": "查看",
        "was": "是",
        "Waterfall": "瀑布",
        "Waterway": "水道",
        "Weapons": "武器",
        "when": "当",
        "When": "当",
        "whisper": "密语",
        "who": "的玩家",
        "Winner": "获胜者",
        "wish": "想要",
        "XP": "经验",
        "yet": "尚未",
        "yourself": "自己",
        "Ability": "能力",
        "Accept": "接受",
        "Accepted": "已接受",
        "Activate": "激活",
        "Activated": "已激活",
        "Active": "开启",
        "Add": "添加",
        "Additional": "额外",
        "Adult": "成人",
        "After": "之后",
        "Arena": "竞技场",
        "Apply": "应用",
        "Available": "可用",
        "Bank": "银行",
        "Be": "被",
        "Begins": "开始",
        "Busy": "忙碌",
        "Buy": "购买",
        "Cancel": "取消",
        "Cancelled": "已取消",
        "Cannot": "无法",
        "Can": "可以",
        "Charge": "充值",
        "Chat": "聊天",
        "Check": "确认",
        "Choose": "选择",
        "Click": "点击",
        "Closed": "已关闭",
        "Combat": "战斗",
        "Common": "普通",
        "Complete": "完成",
        "Completed": "已完成",
        "Confirm": "确认",
        "Connection": "连接",
        "Consumables": "消耗品",
        "Consume": "消耗",
        "Continue": "继续",
        "Cost": "费用",
        "Create": "创建",
        "Created": "已创建",
        "Credit": "点数",
        "Current": "当前",
        "Dead": "死亡",
        "Defeated": "击败",
        "Delete": "删除",
        "Disabled": "已禁用",
        "Discard": "丢弃",
        "Do": "执行",
        "Done": "完成",
        "Drop": "掉落",
        "Duration": "持续时间",
        "Enable": "启用",
        "Enabled": "已启用",
        "Ended": "已结束",
        "Entry": "进入",
        "Error": "错误",
        "Exchange": "交换",
        "Expired": "已过期",
        "Expires": "到期",
        "Fail": "失败",
        "Fainted": "倒下",
        "Field": "场地",
        "Fight": "战斗",
        "Fighters": "战斗者",
        "Find": "查找",
        "Finished": "已结束",
        "Floor": "层",
        "Friend": "好友",
        "Full": "已满",
        "Game": "游戏",
        "Gains": "获得",
        "Get": "获得",
        "Guide": "指南",
        "Has": "已",
        "Have": "拥有",
        "Help": "帮助",
        "Here": "这里",
        "Icon": "图标",
        "Impossible": "无法",
        "Import": "导入",
        "Increased": "增加",
        "Info": "信息",
        "Insert": "放入",
        "Invalid": "无效",
        "Item": "道具",
        "Items": "道具",
        "Join": "参加",
        "Leader": "队长",
        "Leave": "离开",
        "Left": "剩余",
        "Lobby": "大厅",
        "Log": "登出",
        "Lost": "失败",
        "Mail": "邮件",
        "Management": "管理",
        "Match": "比赛",
        "Matches": "比赛",
        "Member": "成员",
        "Members": "成员",
        "Menu": "菜单",
        "Message": "消息",
        "Mobile": "移动",
        "Mode": "模式",
        "Moved": "移动",
        "Need": "需要",
        "Next": "下一",
        "Notice": "通知",
        "Obtained": "已获得",
        "Open": "开放",
        "Option": "选项",
        "Ownership": "所有权",
        "Participant": "参与者",
        "Participants": "参与者",
        "Pay": "支付",
        "Period": "期间",
        "Player": "玩家",
        "Players": "玩家",
        "Possible": "可以",
        "Press": "按下",
        "Progress": "进行中",
        "Purchase": "购买",
        "Quick": "快速",
        "Receive": "领取",
        "Recommended": "推荐",
        "Recover": "恢复",
        "Recovered": "已恢复",
        "Register": "报名",
        "Registered": "已报名",
        "Registration": "报名",
        "Rejected": "被拒绝",
        "Remove": "移除",
        "Renewal": "续期",
        "Renewed": "已续期",
        "Request": "请求",
        "Required": "需要",
        "Requires": "需要",
        "Reset": "重置",
        "Resolved": "已处理",
        "Respawn": "复活",
        "Restore": "恢复",
        "Return": "返回",
        "Rewarded": "获得奖励",
        "Rewards": "奖励",
        "Ring": "擂台",
        "Round": "回合",
        "Rules": "规则",
        "Safe": "安全",
        "Saved": "保存",
        "Score": "分数",
        "Selected": "已选择",
        "Selecting": "选择中",
        "Send": "发送",
        "Settings": "设置",
        "Shared": "共享",
        "Shop": "商店",
        "Side": "侧边",
        "Skill": "技能",
        "Skills": "技能",
        "Slowly": "慢速",
        "Soon": "很快",
        "Special": "特殊",
        "Spending": "花费",
        "Stadium": "赛场",
        "Start": "开始",
        "Started": "已开始",
        "State": "状态",
        "Status": "状态",
        "Stop": "停止",
        "Success": "成功",
        "Successful": "成功",
        "Sure": "确定",
        "Target": "目标",
        "Teleported": "已传送",
        "Timer": "计时器",
        "Title": "称号",
        "Token": "代币",
        "Tokken": "代币",
        "Tooltip": "提示",
        "Unable": "无法",
        "Unknown": "未知",
        "Use": "使用",
        "Used": "已使用",
        "User": "用户",
        "Using": "使用中",
        "Village": "村",
        "Window": "窗口",
        "Windows": "窗口",
        "Win": "胜利",
        "Won": "获胜",
        "World": "世界",
        "Wrong": "错误",
        "Zeni": "索尼",
        "about": "即将",
        "accepted": "已接受",
        "already": "已经",
        "and": "和",
        "another": "另一次",
        "anything": "任何事",
        "at": "在",
        "away": "离开",
        "be": "被",
        "before": "之前",
        "better": "更好",
        "by": "由",
        "can": "可以",
        "can't": "无法",
        "cannot": "无法",
        "created": "已创建",
        "dead": "死亡",
        "do": "执行",
        "doesn't": "不会",
        "don't": "不要",
        "during": "期间",
        "eligible": "符合条件",
        "enough": "足够",
        "for": "用于",
        "from": "来自",
        "get": "获得",
        "got": "已",
        "has": "已",
        "have": "拥有",
        "he": "他",
        "his": "他的",
        "if": "如果",
        "in": "在",
        "into": "到",
        "is": "是",
        "isn't": "不是",
        "it": "它",
        "it's": "现在",
        "kind": "种类",
        "later": "稍后",
        "left": "剩余",
        "less": "低于",
        "made": "建成",
        "might": "可能",
        "must": "必须",
        "new": "新",
        "no": "没有",
        "not": "未",
        "now": "现在",
        "of": "的",
        "off": "下车",
        "on": "在",
        "once": "一次",
        "only": "仅",
        "or": "或",
        "out": "出",
        "please": "请",
        "ready": "准备",
        "right": "当前",
        "same": "相同",
        "should": "应该",
        "slowly": "慢速",
        "soon": "很快",
        "sure": "确定",
        "than": "比",
        "the": "",
        "this": "此",
        "to": "到",
        "up": "上",
        "use": "使用",
        "used": "已使用",
        "while": "时",
        "will": "将",
        "with": "使用",
        "without": "不使用",
        "won't": "不会",
        "world": "世界",
        "you": "你",
        "you're": "你将",
        "you'll": "你将",
        "you've": "你已",
        "your": "你的",
    }
)

PHRASE_MAP.update(
    {
        "Home Teleport": "回城传送",
        "CC Battle Dungeon": "CC战斗副本",
        "Battle Dungeon": "战斗副本",
        "Popo Stone": "波波石",
        "Battle Points": "战斗点数",
        "Battle Rank": "战斗排名",
        "Battle Royale": "大乱斗",
        "Bonus EXP": "经验值加成",
        "Bonus Zeni": "索尼加成",
        "Vehicle speed": "载具速度",
        "New Character": "新角色",
        "Dragon Ball Online": "龙珠Online",
        "Account Creation": "账号创建",
        "Authentication Failure": "验证失败",
        "Aggro List": "仇恨列表",
        "Motion posture": "动作姿势",
        "Air effect": "飞行特效",
        "Air pose": "飞行姿势",
        "Remote Sales": "远程出售",
        "Auction House": "拍卖行",
        "Bag Slot": "背包栏位",
        "Basic Position": "基本姿势",
        "Block cooldown": "格挡冷却",
        "Dojo Finalists": "道场决赛选手",
        "Semi-finals": "半决赛",
        "Semi-final standby": "半决赛待命",
        "Armor Properties": "防具属性",
        "Weapon Properties": "武器属性",
        "Attack Attribute": "攻击属性",
        "Defense Attribute": "防御属性",
        "Accelerated flying": "加速飞行",
        "All Skills": "所有技能",
        "Application completed": "申请完成",
        "Application Period": "申请期间",
        "Battle ended": "战斗结束",
        "Budokai Announcement": "武道会公告",
        "Capsule kit": "胶囊工具包",
        "Cash Coins": "现金币",
        "CC Battle Dungeon": "CC战斗副本",
        "Change Appearance": "改变外观",
        "Change Attributes": "改变属性",
        "Change Channel": "切换频道",
        "Chat Server": "聊天服务器",
        "Cost Zeni": "花费索尼",
        "Cost Tokken": "花费代币",
        "Dragon Ball Online": "龙珠Online",
        "Dragon Ball Scramble": "龙珠争夺战",
        "Dungeon Complete": "副本完成",
        "Entry Time": "入场时间",
        "Event window": "活动窗口",
        "Free-for-all": "自由拾取",
        "Free for all": "自由拾取",
        "Character Server": "角色服务器",
        "Community Server": "社区服务器",
        "Game Check": "游戏检查",
        "Guild Rename": "公会改名",
        "Red Ribbon HQ": "红缎带军总部",
        "Red Pants HQ": "红裤军总部",
        "West City": "西都",
        "Dragon Cave": "龙洞",
        "HoiPoi Mine": "HoiPoi矿山",
        "Underground Waterway": "地下水道",
        "Yahoi Fortress": "雅霍伊要塞",
        "Aria Waterfall Cave": "阿利亚瀑布洞穴",
        "Dungeon Choice Rules": "副本选择规则",
        "Change Item PROP": "更改道具属性",
        "Success Rate": "成功率",
        "On success": "成功时",
        "On failure": "失败时",
        "No sacrifice item required": "不需要辅助道具",
        "Buff Removal": "移除增益",
        "Away Status": "离开状态",
        "Away Mode": "离开模式",
        "Drop Rate": "掉落率",
        "Cooldown Reduced": "冷却减少",
        "extra XP": "额外经验",
        "Hit ESC to skip": "按 ESC 跳过",
        "last whisper": "上一条密语",
        "Fight rules": "战斗规则",
        "Go to": "前往",
        "Home Teleport": "回城传送",
        "HoiPoi": "HoiPoi",
        "Log Out": "登出",
        "Match Info": "比赛信息",
        "Mobile item": "移动道具",
        "Party Leader": "队长",
        "Item Looting": "道具分配",
        "By Grade": "按品质",
        "By Rating": "按品质",
        "Zeni Distribution": "索尼分配",
        "Divide Equally": "平均分配",
        "Item Divide": "道具分配",
        "Loot:": "拾取:",
        "Popo Stone": "波波石",
        "Popostone": "波波石",
        "Quick Buy": "快速购买",
        "Ranked Battle": "排位战",
        "Receive Cash Coins": "领取现金币",
        "Registration Cancel": "取消报名",
        "Scramble Request": "争夺战请求",
        "Selected element": "已选属性",
        "Shared Warehouse": "共享仓库",
        "Skill Point": "技能点",
        "SP Reset": "SP重置",
        "Tension Control": "斗志控制",
        "Tension Points": "斗志点数",
        "Time Machine Quest": "时光机任务",
        "Tournament Players": "锦标赛选手",
        "World Ranking Points": "世界排名点数",
        "battle dungeon": "战斗副本",
        "bring you back": "让你复活",
        "change channel": "切换频道",
        "credit for first": "先充值点数",
        "do anything": "进行操作",
        "fight enemies": "与敌人战斗",
        "for better reward": "获得更好奖励",
        "in progress": "进行中",
        "in your inventory": "在你的背包中",
        "left to leave party": "左侧离开队伍",
        "on ground": "在地面",
        "away state": "离开状态",
        "far away": "距离太远",
        "right away": "立即",
        "same kind of item": "同类道具",
        "status bar": "状态栏",
        "take reward": "领取奖励",
        "the bank slot": "银行栏位",
        "the capsule kit": "胶囊工具包",
        "the item": "该道具",
        "the item right away": "立即购买该道具",
        "the selected item": "选中的道具",
        "to activate": "以激活",
        "to be active": "处于激活状态",
        "trying again": "重试",
        "will be removed": "将被移除",
        "will start soon": "即将开始",
        "will start": "将开始",
        "you can't": "你无法",
        "you can": "你可以",
        "you must": "你必须",
        "you want": "你想",
    }
)


PRINTF_RE = re.compile(r"%(?:\d+\$)?[+#0\- ]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]?[diuoxXfFeEgGaAcspn%]")
TAG_RE = re.compile(
    r"\[(?:"
    r"/?(?:font|align|br|p|s|r|g)(?:\s+[^\]]*)?"
    r"|/?w(?:\s+ID)?"
    r"|\\font"
    r"|size\s*=[^\]]+"
    r")\]",
    re.IGNORECASE,
)
MALFORMED_TAG_RE = re.compile(r"(?<!\[)font\s+size\s*=\s*\"[^\"]+\"\s+color\s*=\s*\"[^\"]+\"\]", re.IGNORECASE)
ESCAPED_NEWLINE_RE = re.compile(r"\\n|\r\n|\r|\n")
PROTECT_RE = re.compile(
    f"{PRINTF_RE.pattern}|{TAG_RE.pattern}|{MALFORMED_TAG_RE.pattern}|{ESCAPED_NEWLINE_RE.pattern}",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"\{\{\d+\}\}")
REMAINING_ENGLISH_RE = re.compile(r"\b[A-Za-z][A-Za-z']*(?:[ ,.!?;:/()+\-]+[A-Za-z][A-Za-z']*){2,}\b")
ALLOWED_REMAINING_ENGLISH_RE = re.compile(
    r"^(?:"
    r"N/A|NPC|DBO|SP|LP|EP|EXP|RP|AP|CC|DWC|FFA|PvP|K\.O|HoiPoi|Popo|Lv\.?\d*|Rank|Set"
    r"|[A-Z]{1,4}\d*"
    r")$"
)
ALLOWED_ASCII_WORD_RE = re.compile(
    r"^(?:"
    r"N/A|NPC|DBO|SP|LP|EP|EXP|RP|AP|CC|CCBD|DWC|FFA|PvP|PVP|K\.O|GM|TMQ|VIP|"
    r"HoiPoi|Popo|Wagu|Mudosa|Lv\.?|Lv|RO\d+|[A-Z]{1,5}\d*|\d+[A-Za-z]*"
    r")$"
)

SENTENCE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in (
        (r"^\s*(\{\{\d+\}\})\s+CLEARED\s+CC Battle Dungeon\s+(\d+)\s+Floor\s*$", r"\1 已通关 CC战斗副本\2层"),
        (r"^\s*CC Battle Dungeon\s+(\d+)\s+Floor\s+WAS\s+CLEARED\s*$", r"CC战斗副本\1层已通关"),
        (r"^\s*(\{\{\d+\}\})\s+ready up\s*$", r"\1 已准备"),
        (r"^\s*(\{\{\d+\}\})\s+Score Results\s+(\{\{\d+\}\})\s*$", r"\1 分数结果 \2"),
        (r"^\s*(\{\{\d+\}\})\s+Team Result\s*\(\s*(\{\{\d+\}\})\s*\)\s*$", r"\1 团队结果（\2）"),
        (r"^\s*(\{\{\d+\}\})\s+Won\s+(\{\{\d+\}\})\s*$", r"\1 获胜 \2"),
        (r"^\s*(\{\{\d+\}\})\s+team has won\s+(\{\{\d+\}\})\s*$", r"\1 队伍获胜 \2"),
        (r"^\s*(\{\{\d+\}\})\s+Killed\s+(\{\{\d+\}\})\s*$", r"\1 击败了 \2"),
        (r"^\s*(\{\{\d+\}\})\s+is over\s*$", r"\1 已结束"),
        (r"^\s*(\{\{\d+\}\})\s+registration ends in\s+(\{\{\d+\}\})\s*\.?\s*$", r"\1 报名将在 \2 后结束。"),
        (r"^\s*(\{\{\d+\}\})\s+finals start in\s+(\{\{\d+\}\})\s*\.?\s*$", r"\1 决赛将在 \2 后开始。"),
        (r"^\s*(\{\{\d+\}\})\s+qualifiers will start in\s+(\{\{\d+\}\})\s*\.?\s*$", r"\1 预选赛将在 \2 后开始。"),
        (r"^\s*(\{\{\d+\}\})\s+semi-finals start in\s+(\{\{\d+\}\})\s*\.?\s*$", r"\1 半决赛将在 \2 后开始。"),
        (r"^\s*(\{\{\d+\}\})\s+Application completed\s*\.?\s*$", r"\1 申请完成。"),
        (r"^\s*(\{\{\d+\}\})'s Number\s*:\s*$", r"\1 的号码："),
        (r"^\s*(\{\{\d+\}\})\s+Stadium\s*$", r"\1 赛场"),
        (r"^\s*(\{\{\d+\}\})\s+day\s*$", r"\1 天"),
        (r"^\s*(\{\{\d+\}\})\s+hour\s*$", r"\1 小时"),
        (r"^\s*(\{\{\d+\}\})\s+minute\s*$", r"\1 分钟"),
        (r"^\s*(\{\{\d+\}\})\s+second\s*$", r"\1 秒"),
        (r"^\s*Damage\s+(.+)\s*$", r"伤害 \1"),
        (r"^\s*Defense\s+(.+)\s*$", r"防御 \1"),
        (r"^\s*Attack Attribute\s*:\s*(.+)\s*$", r"攻击属性：\1"),
        (r"^\s*Defense Attribute\s*:\s*(.+)\s*$", r"防御属性：\1"),
        (r"^\s*Floor\s+(.+)\s+complete\s*$", r"第 \1 层完成"),
        (r"^\s*Level\s+(.+)\s*$", r"等级 \1"),
        (r"^\s*Lv\.\s*(.+)\s*$", r"Lv.\1"),
        (r"^\s*Cost\s*:\s*(.+)\s*$", r"费用：\1"),
        (r"^\s*Item\s*:\s*(.+)\s*$", r"道具：\1"),
        (r"^\s*Zeni\s*:\s*(.+)\s*$", r"索尼：\1"),
        (r"^\s*Entry Time\s*:\s*(.+)\s+left\s*\.?\s*$", r"入场剩余时间：\1。"),
        (r"^\s*Next round\s*:\s*(.+)\s*$", r"下一轮：\1"),
        (r"^\s*(\d+)(?:st|nd|rd|th)\s*:\s*(.+)\s*$", r"第\1名：\2"),
        (r"^\s*(\d+)s\s+(.+)\s+goes into the arena\s*$", r"\1秒后 \2 进入竞技场"),
    )
)

BRACKET_OK_REPLACEMENTS = {
    "[Ok]": "[确定]",
    "[OK]": "[确定]",
    "[Cancel]": "[取消]",
}


def protect_tokens(text: str) -> tuple[str, list[str]]:
    tokens: list[str] = []

    def repl(match: re.Match[str]) -> str:
        tokens.append(match.group(0))
        return f"{{{{{len(tokens) - 1}}}}}"

    protected = PROTECT_RE.sub(repl, text)
    return protected, tokens


def restore_tokens(text: str, tokens: list[str]) -> str:
    for index, token in enumerate(tokens):
        text = text.replace(f"{{{{{index}}}}}", token)
    return text


def is_acceptable_batch_result(text: str) -> bool:
    stripped = TAG_RE.sub(" ", text)
    stripped = PRINTF_RE.sub(" ", stripped)
    stripped = re.sub(r"\[[A-Za-z0-9 %.:+\\/-]+\]", " ", stripped)
    if REMAINING_ENGLISH_RE.search(stripped):
        return False
    for word in re.findall(r"[A-Za-z][A-Za-z'.]*\d*", stripped):
        if not ALLOWED_REMAINING_ENGLISH_RE.fullmatch(word):
            return False
    return True


def translate_markup_text(text: str) -> str | None:
    protected, tokens = protect_tokens(text)
    translated = translate_protected(protected)
    if not translated or translated == protected:
        return None
    translated = restore_tokens(translated, tokens)
    if not is_acceptable_batch_result(translated):
        return None
    return translated


def translate_plain(text: str) -> str | None:
    source = text.strip()
    if not source:
        return text
    if source in EXACT_MAP:
        return preserve_outer_space(text, EXACT_MAP[source])
    if source in PHRASE_MAP:
        return preserve_outer_space(text, PHRASE_MAP[source])
    named = translate_name(source)
    if named and not re.search(r"[A-Za-z]{3,}", named):
        return preserve_outer_space(text, named)

    simple = simple_sentence(source)
    if simple:
        if not is_acceptable_batch_result(simple):
            return None
        return preserve_outer_space(text, simple)
    return None


def force_translate_text(text: str) -> str:
    source = text.strip()
    if not source:
        return text
    if source in EXACT_MAP:
        return preserve_outer_space(text, EXACT_MAP[source])
    protected, tokens = protect_tokens(text)
    translated = translate_protected(protected)
    if not translated:
        translated = protected
    translated = restore_tokens(translated, tokens)
    translated = normalize_output_text(translated)
    return translated if translated.strip() else text


def translate_protected(text: str) -> str:
    if not text:
        return text
    original = text
    text = replace_bracket_ok(text)
    exact = EXACT_MAP.get(text.strip())
    if exact:
        return preserve_outer_space(text, exact)
    for pattern, replacement in SENTENCE_PATTERNS:
        if pattern.search(text):
            text = pattern.sub(replacement, text)
            return cleanup_chinese_spacing(text)
    named = translate_name(text.strip())
    if named and not re.search(r"[A-Za-z]{3,}", named):
        return preserve_outer_space(text, named)
    text = replace_phrases(text)
    text = replace_words(text)
    text = cleanup_chinese_spacing(text)
    return text if text != original else original


def replace_bracket_ok(text: str) -> str:
    for source, target in BRACKET_OK_REPLACEMENTS.items():
        text = text.replace(source, target)
    return text


def replace_phrases(text: str) -> str:
    for source, target in sorted(PHRASE_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if not source:
            continue
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(source)}(?![A-Za-z0-9])", re.IGNORECASE)
        text = pattern.sub(target, text)
    phrase_exact = {
        "You've failed to connect to": "你连接失败：",
        "the authentication server": "验证服务器",
        "Please try again in a few minutes": "请几分钟后再试",
        "Your account has been created and should": "你的账号已创建，并且应该",
        "now have access to": "现在可以访问",
        "It's time to fight": "战斗时间到了",
        "Go to the ring": "前往擂台",
        "Tension control used": "已使用斗志控制",
        "get up to": "最多获得",
        "Learn how to fight": "学习战斗方式",
        "dojo imprint acquisition": "获得道场印记",
        "points to go": "点数前进",
        "Can't create a party in a fight": "战斗中无法创建队伍",
        "Go to the fight": "前往战斗",
        "will send a challenge": "将发送挑战",
        "When the challenge is accepted": "挑战被接受后",
        "you'll have to fight": "你必须进行战斗",
        "When you send a challenge": "当你发送挑战时",
        "You must win": "你必须获胜",
        "Or be ready to laughed at": "否则就等着被嘲笑",
        "Know your enemy": "了解你的敌人",
        "Match might be rejected": "比赛可能被拒绝",
        "Players who prove to be the best": "证明自己最强的玩家",
        "Will go to the": "将进入",
        "qualification spots": "资格席位",
        "Fight to Qualify": "战斗以取得资格",
        "Check the following": "请确认以下内容",
        "best Tournament": "最强锦标赛",
        "in the world": "世界上",
        "make sure": "确认",
        "You're here": "你在这里",
        "If you activate you won't be able to disable": "激活后将无法禁用",
        "This item will be removed": "该道具将被移除",
        "bank slot will be made available": "银行栏位将开放",
        "after clicking": "点击后",
        "Are you sure you want to activate the item": "确定要激活该道具吗",
        "The members in the Dojo": "道场成员",
        "are responsible to": "负责",
        "keep the Dojo safe": "守护道场安全",
        "When the Dojo is made": "道场建成后",
        "special content and benefits": "特殊内容和福利",
        "To get a Dojo": "要获得道场",
        "buy with points": "用点数购买",
        "Buy a Dojo": "购买道场",
        "Change the time and become an adult or child": "改变时间，变成成人或儿童",
        "After successful change": "改变成功后",
        "it can't be restored": "将无法恢复",
        "without another use of the item": "除非再次使用该道具",
        "Change appearance now": "现在改变外观吗",
        "Challenge from Dojo": "来自道场的挑战",
        "prove your worth": "证明你的价值",
        "Fight for the Dojo's fate": "为道场命运而战",
        "If you Reject": "如果你拒绝",
        "You can't win any Zeni": "你无法获得任何索尼",
        "Accept Challenge": "接受挑战",
        "You can purchase the item right away": "你可以立即购买该道具",
        "You've left the guild": "你已离开公会",
        "left the Party": "离开了队伍",
        "left the party": "离开了队伍",
        "Target is in away state": "目标处于离开状态",
        "Too far away": "距离太远",
        "Too far away from a Popo Stone": "离波波石太远",
        "Party member is too far away to share quest": "队员距离太远，无法共享任务",
        "Shop is too far away": "离商店太远",
        "You're too far away from the target": "你离目标太远",
        "the durability got renewed": "耐久度会被刷新",
        "Do you want to buy it": "你想购买吗",
        "Any level": "任意等级",
        "can reset once a week": "每周可重置一次",
        "SP recovered": "返还SP",
        "All Skills will be removed": "所有技能将被移除",
        "Reset the Skills now": "现在重置技能吗",
        "Use to charge your credit": "用于充值点数",
        "After you import it to your": "导入到你的",
        "you must use it to": "你必须使用它来",
        "After this you can use in shop": "之后即可在商店使用",
        "Are you sure you want to import it": "确定要导入吗",
        "Participants who enter": "进入的参与者",
        "will fight enemies on each floor": "将在每层与敌人战斗",
        "Each floor's difficulty is different": "每层难度不同",
        "Every 5th floor will be a boss floor": "每5层为首领层",
        "once boss is defeated": "首领被击败后",
        "you have the option to": "你可以选择",
        "take reward and leave": "领取奖励并离开",
        "or carry on": "或继续挑战",
        "Higher floors give better rewards": "层数越高奖励越好",
        "If management upgrade": "如果进行管理升级",
        "You can add special features": "可以添加特殊功能",
        "Click ok to use the item": "点击确定使用道具",
        "Click ok to pay": "点击确定支付",
        "All Skills will reset": "所有技能将重置",
        "Item used": "使用道具",
        "Saved SP": "保存的SP",
        "Skills without SP don't reset": "未消耗SP的技能不会重置",
        "Reset Skills now": "现在重置技能吗",
        "Move the selected item to": "将选中道具移动到",
        "When moved into": "移动到",
        "and the same item already exists": "且已有相同道具时",
        "Are you sure you want to move an item": "确定要移动道具吗",
        "Can't do anything while dead": "死亡时无法进行操作",
        "Wait for a friend": "等待好友",
        "To bring you back": "将你复活",
        "or go to": "或前往",
        "Select an action": "选择操作",
        "Please wait": "请等待",
        "for the timer": "计时器",
        "you can't respawn": "你无法复活",
        "until the timer": "直到计时器",
        "runs out": "结束",
        "Stay in this world": "留在当前世界",
        "This item period expires": "该道具期限将到期",
        "without extending the period": "且不延长期限",
        "Renewal is possible without discard": "无需丢弃也可以续期",
        "Do you really want to discard": "真的要丢弃吗",
        "The item will got in your inventory": "道具将进入你的背包",
    }
    for source, target in sorted(phrase_exact.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(source)}(?![A-Za-z0-9])", re.IGNORECASE)
        text = pattern.sub(target, text)
    return text


def replace_words(text: str) -> str:
    parts = re.split(r"(\{\{\d+\}\}|[A-Za-z][A-Za-z']*|[0-9]+(?:st|nd|rd|th)?|%%|[^\w{}]+)", text)
    output: list[str] = []
    for part in parts:
        if not part:
            continue
        if TOKEN_RE.fullmatch(part):
            output.append(part)
            continue
        if re.fullmatch(r"[0-9]+(?:st|nd|rd|th)?", part):
            output.append(part)
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z']*", part):
            translated = lookup_word(part)
            output.append(translated)
            continue
        output.append(normalize_punctuation(part))
    return "".join(output)


@lru_cache(maxsize=4096)
def lookup_word(word: str) -> str:
    if ALLOWED_ASCII_WORD_RE.fullmatch(word):
        return word
    for key in (word, word.title(), word.lower(), word.upper()):
        if key in WORD_MAP:
            return WORD_MAP[key]
    return word


def normalize_punctuation(text: str) -> str:
    return (
        text.replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("•", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("：", ":")
    )


def normalize_output_text(text: str) -> str:
    text = normalize_punctuation(text)
    return cleanup_chinese_spacing(text)


def cleanup_chinese_spacing(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([，。！？；：、）])", r"\1", text)
    text = re.sub(r"([（])\s+", r"\1", text)
    text = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", text)
    text = re.sub(r"([\u4e00-\u9fff])\s+([,.!?;:])", r"\1\2", text)
    text = re.sub(r"([,.!?;:])\s+([\u4e00-\u9fff])", r"\1\2", text)
    text = text.replace(" :", "：").replace(": ", "：")
    text = text.replace(" ,", "，").replace(" .", "。").replace(" ?", "？").replace(" !", "！")
    text = text.replace(",", "，").replace("?", "？")
    text = text.replace("!", "！")
    text = re.sub(r"([\u4e00-\u9fff])\.($|\s|\{\{)", r"\1。\2", text)
    text = text.replace("  ", " ")
    return text.strip()


def preserve_outer_space(original: str, translated: str) -> str:
    prefix = original[: len(original) - len(original.lstrip())]
    suffix = original[len(original.rstrip()) :]
    return f"{prefix}{translated}{suffix}"


def simple_sentence(text: str) -> str | None:
    patterns = [
        (r"Damage (.+)", r"伤害 \1"),
        (r"Defense (.+)", r"防御 \1"),
        (r"(.+) Floor", r"\1层"),
        (r"(.+) standby", r"\1待命"),
        (r"Cancel (.+)", r"取消\1"),
        (r"Change (.+)", r"更改\1"),
        (r"(.+) Available", r"可使用\1"),
    ]
    for pattern, repl in patterns:
        match = re.fullmatch(pattern, text)
        if not match:
            continue
        rendered = re.sub(pattern, repl, text)
        translated = translate_words(rendered)
        if translated:
            return translated
    return translate_words(text)


def translate_words(text: str) -> str | None:
    if not re.fullmatch(r"[A-Za-z0-9 %.':/()+\-]+", text):
        return None
    output: list[str] = []
    changed = False
    for token in re.findall(r"%\w|%%|\d+|[A-Za-z']+|[^A-Za-z0-9%]+", text):
        if token in {"%%"} or re.fullmatch(r"%\w", token) or token.isdigit():
            output.append(token)
        elif re.fullmatch(r"[A-Za-z']+", token):
            translated = WORD_MAP.get(token) or WORD_MAP.get(token.title())
            if not translated:
                return None
            output.append(translated)
            changed = True
        else:
            output.append(token)
    if not changed:
        return None
    return "".join(output).replace("  ", " ").strip()


def translate_text(text: str) -> str | None:
    if TAG_RE.search(text):
        return translate_markup_text(text)
    return translate_plain(text)


@dataclass(frozen=True)
class TranslationStats:
    selected: int
    filled: int
    empty_before: int
    empty_after: int
    reused_existing: int
    skipped: int


def queue_key(row: dict[str, str]) -> tuple[str, str]:
    return ((row.get("文件") or "").strip(), (row.get("原文") or "").strip())


def is_internal_identifier(text: str) -> bool:
    return INTERNAL_IDENTIFIER_RE.fullmatch(text.strip()) is not None


def translate_queue(
    *,
    queue_path: Path = QUEUE_PATH,
    out_path: Path | None = None,
    translations_path: Path = TRANSLATIONS_PATH,
    fill_all: bool = False,
    replace_existing: bool = False,
    ignore_existing_map: bool = False,
    only_keys: set[tuple[str, str]] | None = None,
) -> TranslationStats:
    queue_path = queue_path.resolve()
    out_path = (out_path or queue_path).resolve()
    with queue_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    if "填写中文" not in fieldnames:
        raise SystemExit("Missing 填写中文 column")

    existing = {} if ignore_existing_map else load_existing_translation_map(translations_path)
    selected = 0
    filled = 0
    empty_before = 0
    empty_after = 0
    reused = 0
    skipped = 0
    for row in rows:
        if only_keys is not None and queue_key(row) not in only_keys:
            continue
        selected += 1
        current = row.get("填写中文") or ""
        source = row.get("原文") or ""
        if is_internal_identifier(source):
            skipped += 1
            if not current.strip():
                empty_before += 1
                empty_after += 1
            continue
        if current.strip() and not replace_existing:
            skipped += 1
            continue
        if not current.strip():
            empty_before += 1
        stripped_source = source.strip()
        if stripped_source in EXACT_MAP:
            translated = preserve_outer_space(source, EXACT_MAP[stripped_source])
        else:
            translated = existing.get(stripped_source)
        if translated and stripped_source not in EXACT_MAP:
            reused += 1
        else:
            translated = translated or (force_translate_text(source) if fill_all else translate_text(source))
        if translated:
            row["填写中文"] = translated
            filled += 1
        else:
            if not current.strip():
                empty_after += 1
            skipped += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    return TranslationStats(selected, filled, empty_before, empty_after, reused, skipped)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch-fill safe translations in data/new_translations.tsv")
    parser.add_argument(
        "--fill-all",
        action="store_true",
        help="Fill every empty cell, including long text, using fallback phrase/word rules.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Recompute existing filled cells too.",
    )
    parser.add_argument(
        "--ignore-existing-map",
        action="store_true",
        help="Do not reuse translations.tsv exact source matches.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=QUEUE_PATH,
        help="Output path. Defaults to overwriting data/new_translations.tsv.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    stats = translate_queue(
        queue_path=QUEUE_PATH,
        out_path=out_path,
        fill_all=args.fill_all,
        replace_existing=args.replace_existing,
        ignore_existing_map=args.ignore_existing_map,
    )
    print(f"selected={stats.selected}")
    print(f"filled={stats.filled}")
    print(f"empty_before={stats.empty_before}")
    print(f"empty_after={stats.empty_after}")
    print(f"reused_existing={stats.reused_existing}")
    print(f"skipped={stats.skipped}")
    print(f"path={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
