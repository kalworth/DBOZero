# Translation Conflicts Review

这个文件给人看。它只列同一原文出现多个中文译法的情况。

Total conflicts: 16

## 1. Normal

- 原文 hash: `45e118d0563e`
- 出现位置: 6
- 现有译法: 普通 | 正常
- 建议处理: 这是多义词，不能全局替换；按 key 场景逐条确认。

位置：
- `lang0/lang0.pak/DST_ITEM_GRADE_NORMAL (legacy/translations/lang0_overrides.tsv:38)` -> 普通
- `lang0/lang0.pak/DST_LOBBY_SERVER_NORMAL (legacy/translations/lang0_overrides.tsv:124)` -> 正常
- `lang0/lang0.pak/DST_OPTION_CHATTING_ADDED_NORMAL (legacy/translations/lang0_overrides.tsv:299)` -> 普通
- `lang0/lang0.pak/DST_OPTION_CHATTING_BASIC_NORMAL (legacy/translations/lang0_overrides.tsv:307)` -> 普通
- `lang0/lang0.pak/DST_OPTION_DROPFILTER_NORMAL (legacy/translations/lang0_overrides.tsv:416)` -> 普通
- `lang0/lang0.pak/DST_MARKET_NORMALTYPE (legacy/translations/lang0_overrides.tsv:676)` -> 普通

## 2. Whisper

- 原文 hash: `c010a73e4748`
- 出现位置: 4
- 现有译法: 密语 | 私聊
- 建议处理: 建议聊天功能统一为“私聊”。

位置：
- `lang0/lang0.pak/DST_OPTION_CHATTING_ADDED_WISPHER (legacy/translations/lang0_overrides.tsv:305)` -> 密语
- `lang0/lang0.pak/DST_OPTION_CHATTING_BASIC_WISPHER (legacy/translations/lang0_overrides.tsv:313)` -> 密语
- `lang0/lang0.pak/DST_POPUPMENU_SEND_WHISPER (legacy/translations/lang0_overrides.tsv:598)` -> 密语
- `lang0/lang0.pak/DST_FRIEND_WHISPER (legacy/translations/lang0_overrides.tsv:870)` -> 私聊

## 3. Scouter

- 原文 hash: `8bcb090d6225`
- 出现位置: 4
- 现有译法: 史考特 | 探测器
- 建议处理: 建议统一为“探测器”，旧的“史考特”应淘汰。

位置：
- `taiwan/local_data.dat/DST_EQUIP_SLOT_TYPE_SCOUTER (legacy/translations/overrides.tsv:164)` -> 探测器
- `lang0/lang0.pak/DST_EQUIP_SLOT_TYPE_SCOUTER (legacy/translations/lang0_overrides.tsv:97)` -> 史考特
- `lang0/lang0.pak/DST_OPTION_CONTROL_ACTION_WINDOW_SCOUTER (legacy/translations/lang0_overrides.tsv:392)` -> 史考特
- `lang0/lang0.pak/DST_MARKET_SCOUTER (legacy/translations/lang0_overrides.tsv:689)` -> 史考特

## 4. Namek

- 原文 hash: `fa4790545002`
- 出现位置: 4
- 现有译法: 那美 | 那美克
- 建议处理: 建议统一为“那美克”。

位置：
- `taiwan/table_text_all_data.rdf/4:6001515:0 (legacy/translations/overrides.tsv:254)` -> 那美克
- `lang0/lang0.pak/DST_MOB_TYPE_NAMEC (legacy/translations/lang0_overrides.tsv:75)` -> 那美
- `lang0/lang0.pak/DST_NAMEK (legacy/translations/lang0_overrides.tsv:134)` -> 那美
- `lang0/lang0.pak/DST_NAMEK (legacy/translations/lang0_overrides.tsv:619)` -> 那美

## 5. Weapon

- 原文 hash: `ead533685e26`
- 出现位置: 3
- 现有译法: 主武器 | 武器
- 建议处理: 建议按场景区分：装备槽用“主武器”，泛称/市场用“武器”。

位置：
- `taiwan/local_data.dat/DST_EQUIP_SLOT_TYPE_HAND (legacy/translations/overrides.tsv:163)` -> 武器
- `lang0/lang0.pak/DST_EQUIP_SLOT_TYPE_HAND (legacy/translations/lang0_overrides.tsv:90)` -> 主武器
- `lang0/lang0.pak/DST_MARKET_WEAPON (legacy/translations/lang0_overrides.tsv:713)` -> 武器

## 6. No-Bank

- 原文 hash: `fe517aab1048`
- 出现位置: 3
- 现有译法: 禁仓库 | 禁公仓
- 建议处理: 建议统一为“禁仓库”。

位置：
- `lang0/lang0.pak/DST_ITEM_LIMITED_STORE_COMMON_WAREHOUSE (legacy/translations/lang0_overrides.tsv:67)` -> 禁仓库
- `lang0/lang0.pak/DST_ITEM_LIMITED_STORE_GUILD_WAREHOUSE (legacy/translations/lang0_overrides.tsv:68)` -> 禁公仓
- `lang0/lang0.pak/DST_ITEM_LIMITED_STORE_WAREHOUSE (legacy/translations/lang0_overrides.tsv:69)` -> 禁仓库

## 7. Block

- 原文 hash: `82dd2cdf36f9`
- 出现位置: 3
- 现有译法: 屏蔽 | 格挡
- 建议处理: 这是多义词，不能全局替换；按 key 场景逐条确认。

位置：
- `lang0/lang0.pak/DST_OPTION_CONTROL_ACTION_AVATAR_BLOCKING (legacy/translations/lang0_overrides.tsv:326)` -> 格挡
- `lang0/lang0.pak/DST_POPUPMENU_USER_BLOCK (legacy/translations/lang0_overrides.tsv:599)` -> 屏蔽
- `lang0/lang0.pak/DST_FRIEND_BLOCK (legacy/translations/lang0_overrides.tsv:843)` -> 屏蔽

## 8. Trumpet

- 原文 hash: `66c3284825be`
- 出现位置: 2
- 现有译法: 乐器 | 号角
- 建议处理: 二选一：确认一个主译法后写入 glossary 或逐 key 固定。

位置：
- `lang0/lang0.pak/DST_INSTRUMENT (legacy/translations/lang0_overrides.tsv:735)` -> 乐器
- `tbl/tbl0.pak/0x012732BD (legacy/translations/tbl_overrides.tsv:264)` -> 号角

## 9. Start

- 原文 hash: `952f375412e8`
- 出现位置: 2
- 现有译法: 开始 | 登录
- 建议处理: 这是多义词，不能全局替换；按 key 场景逐条确认。

位置：
- `lang0/lang0.pak/DST_LOGIN (legacy/translations/lang0_overrides.tsv:24)` -> 登录
- `lang0/lang0.pak/DST_LOBBY_GAME_START (legacy/translations/lang0_overrides.tsv:83)` -> 开始

## 10. Receive items and Zeni from eligible mail (up to 6 per use, 15s cooldown).

- 原文 hash: `f3ab123119b0`
- 出现位置: 2
- 现有译法: 从符合条件的邮件领取物品和索尼(每次最多6封，冷却15秒)。 | 从符合条件的邮件领取道具和索尼（每次最多6封，冷却15秒）。
- 建议处理: 建议货币统一为“索尼”，同时保留占位符。

位置：
- `taiwan/local_data.dat/DST_MAILSYSTEM_TOOLTIP_RECEIVE_ALL (legacy/translations/overrides.tsv:112)` -> 从符合条件的邮件领取道具和索尼（每次最多6封，冷却15秒）。
- `lang0/lang0.pak/DST_MAILSYSTEM_TOOLTIP_RECEIVE_ALL (legacy/translations/lang0_overrides.tsv:822)` -> 从符合条件的邮件领取物品和索尼(每次最多6封，冷却15秒)。

## 11. Party Only

- 原文 hash: `58d840480dff`
- 出现位置: 2
- 现有译法: 仅队伍 | 组队专用
- 建议处理: 建议统一为“仅队伍”。

位置：
- `taiwan/local_data.dat/DST_OPTION_PERF_PLAYER_FILTER_PARTY (legacy/translations/overrides.tsv:156)` -> 组队专用
- `lang0/lang0.pak/DST_OPTION_PERF_PLAYER_FILTER_PARTY (legacy/translations/lang0_overrides.tsv:476)` -> 仅队伍

## 12. Filter Legendary Items 

- 原文 hash: `b105e60d1ed5`
- 出现位置: 2
- 现有译法: 过滤传说物品 | 过滤龙珠物品
- 建议处理: 二选一：确认一个主译法后写入 glossary 或逐 key 固定。

位置：
- `lang0/lang0.pak/DST_OPTION_DROPFILTER_TOOLTIP_LEGENDARY (legacy/translations/lang0_overrides.tsv:438)` -> 过滤传说物品
- `lang0/lang0.pak/DST_OPTION_DROPFILTER_TOOLTIP_DRAGONBALL (legacy/translations/lang0_overrides.tsv:439)` -> 过滤龙珠物品

## 13. Charge

- 原文 hash: `d4e1aee46cda`
- 出现位置: 2
- 现有译法: 蓄气 | 费用
- 建议处理: 这是多义词，不能全局替换；按 key 场景逐条确认。

位置：
- `lang0/lang0.pak/DST_OPTION_CONTROL_ACTION_AVATAR_CHARGE (legacy/translations/lang0_overrides.tsv:327)` -> 蓄气
- `lang0/lang0.pak/DST_MARKET_SELL_PRICE (legacy/translations/lang0_overrides.tsv:700)` -> 费用

## 14. All Classes

- 原文 hash: `0e75c6a2260c`
- 出现位置: 2
- 现有译法: 全职业 | 所有职业
- 建议处理: 建议统一为“全职业”。

位置：
- `lang0/lang0.pak/DST_ITEM_ALL_RACE (legacy/translations/lang0_overrides.tsv:73)` -> 所有职业
- `lang0/lang0.pak/DST_MARKET_ALLCLASS (legacy/translations/lang0_overrides.tsv:632)` -> 全职业

## 15. Accessory 2 - Richness

- 原文 hash: `743ac3dc0393`
- 出现位置: 2
- 现有译法: 配件 2 - 光环 | 饰品2 - 富饶
- 建议处理: 二选一：确认一个主译法后写入 glossary 或逐 key 固定。

位置：
- `taiwan/local_data.dat/DST_EQUIP_SLOT_TYPE_ACCESSORY2 (legacy/translations/overrides.tsv:153)` -> 饰品2 - 富饶
- `lang0/lang0.pak/DST_EQUIP_SLOT_TYPE_ACCESSORY2 (legacy/translations/lang0_overrides.tsv:102)` -> 配件 2 - 光环

## 16. %s Zeni

- 原文 hash: `d89500f73efb`
- 出现位置: 2
- 现有译法: %s 索 | %s索尼
- 建议处理: 建议货币统一为“索尼”，同时保留占位符。

位置：
- `taiwan/local_data.dat/DST_DROPITEM_ZENNY (legacy/translations/overrides.tsv:154)` -> %s索尼
- `lang0/lang0.pak/DST_INFOWINDOW_ZENNY (legacy/translations/lang0_overrides.tsv:282)` -> %s 索
