# Phrase-To-Picture Binding

Use this when turning narration into beats, text units, screenshots, and micro-events.

## Extract the Visual Triggers

For each sentence, mark:

- **Concrete nouns:** people, companies, apps, cities, products, webpages, documents, devices, places, prices, objects.
- **Verbs:** open, see, rise, fall, compare, clarify, spread, block, reveal, shrink, expand, switch, pay, drive.
- **Numbers:** time, price, percentage, ranking, distance, inventory, users, growth, cost.
- **Contrast words:** but, however, normal/VIP, before/after, official/user, advertised/actual.
- **Emotion words:** panic, anger, pressure, doubt, relief, unfairness, exhaustion.
- **Evidence words:** announcement, table, screenshot, comment, app page, hot search, official response.

Every important trigger needs a visible answer unless the director intentionally withholds it for suspense.

## Binding Grammar

| Narration trigger | Visual response |
|---|---|
| named app/product/webpage | real screenshot, phone/browser frame, screen recording |
| official statement/news/source | source card, webpage screenshot, quote crop, source label |
| table/rights/comparison | full table first, then row/column highlight and magnifier |
| price/percentage/time | number hero, counter, price card, chart end label |
| rise/fall | line climbs/drops, bars reorder, number ticks, red/green accent |
| open/tap/scroll/search | cursor/tap, screen recording, UI state change |
| reveal/clarify | mask wipe, spotlight, before/after, source replaces rumor |
| spread/chain reaction | map/network/forwarding trail, repeated cards |
| personal pressure | real-life B-roll, bill, commute, work scene, slower camera |
| viewpoint sentence | sparse typography, black/quiet footage, deliberate pause |

## Dynamic Text System

Do not place a whole sentence as one same-size text box when the sentence has hierarchy.

Split text into units:

- `caption`: short subtitle or spoken support, usually bottom-safe.
- `keyword`: one phrase that appears on the word itself.
- `number_hero`: price, percentage, rank, time, cost; often largest element.
- `contrast_label`: normal/VIP, before/after, official/user, cost/price.
- `quote_card`: person or public comment with source/person label.
- `evidence_label`: red "广告", "VIP 专属", "官方说明", "来源".
- `viewpoint_line`: end-card judgment, usually sparse and timed line by line.

Rules:

- Exact Chinese text must be HTML/SVG/canvas text, not baked into generated raster images.
- Text units should normally be generated directly in HyperFrames, not exported as separate image assets.
- Keywords should be tied to objects: on an ad slot, beside a chart endpoint, above a table column, attached to a product page, or over a real scene.
- Use red/large/bold only for true emphasis. If every word is red, nothing is emphasized.
- A number can be the frame's hero. Do not hide it in subtitle size.
- Comments and social reactions can appear like stickers or stacked cards, but keep source and privacy considerations.

## Text Span Contract

Use `text_manifest.json` as the contract for expressive text. A text item may remain a single unit, or it may include `spans` when narration needs keyword-level or word-level emphasis.

Recommended optional fields:

- `sync_phrase`: spoken phrase that triggers the item or span.
- `attach_to`: asset/component/detail ID such as `ref_app_ad_slot`, `chart_price_line`, or `hf_red_box`.
- `hierarchy`: `caption`, `support`, `keyword`, `hero`, `sticker`, or `viewpoint`.
- `motion_preset_id`: named entrance/exit/combo preset from `micro_animation_palette.json`.
- `text_preset_id`: named text styling preset from `micro_animation_palette.json`.
- `emphasis_level`: `low`, `medium`, `high`, or `hero`.
- `avoid_zones`: proof details the text must not cover, such as `source_label`, `table_header`, `chart_axis`, or a concrete `must_show_detail`.
- `persistence_policy`: `hold`, `yield_to_side`, `store_as_chip`, `shrink_stack`, or `exit_intentional`.
- `previous_text_behavior`: how the prior expressive text should yield when a new phrase enters.

Example shape:

```json
{
  "id": "text_price_reason",
  "text": "不是涨价，是成本被推上去了",
  "role": "keyword",
  "beat_id": "B006",
  "start_sec": 12.4,
  "end_sec": 14.2,
  "attach_to": "chart_cost_line",
  "motion_preset_id": "text.keyword_pop",
  "spans": [
    {"text": "不是涨价", "sync_phrase": "不是涨价", "hierarchy": "support", "style": "small_dark"},
    {"text": "成本", "sync_phrase": "成本", "hierarchy": "hero", "text_preset_id": "text.stroke_shadow_hot"},
    {"text": "推上去了", "sync_phrase": "推上去了", "hierarchy": "keyword", "motion_preset_id": "text.short_slide_down"}
  ]
}
```

Do not force spans into every caption. Use spans when mixed hierarchy, timing, or visual attachment makes the beat clearer.

## Flower Text and Persistence

For Chinese social/explainer videos, expressive text should behave more like edited "flower words" than subtitles. The director should prefer:

- keyword-level or word-level hierarchy over a whole sentence in one box;
- live text stroke, outline, shadow, gradient fill, underline, or per-word color over paragraph-level borders;
- one or two hero words that become much larger than support words;
- character or span timing when the spoken rhythm has a clear hit;
- no backing card when outline/stroke/color is enough;
- a backing sticker/pill only when it improves readability or intentionally feels like a label.

When the next flower text appears, the default is not to delete the previous one. Choose one of these behaviors:

- `yield_to_side`: previous text shrinks and moves to a side/corner to make room.
- `store_as_chip`: previous text becomes a small memory chip or evidence tag.
- `shrink_stack`: previous text joins a vertical stack of earlier claims.
- `hold`: previous text stays in place because it is still the focal owner.
- `exit_intentional`: previous text leaves only when the beat function needs a clean reset, proof readability, or emotional silence.

Example: for "被 WPS 背刺了", do not render one same-size bordered sentence. Make "WPS" a hero span, thicken/stroke it, and let "被" / "背刺了" support it with different scale, color, or timing. If the next phrase enters, shrink the whole line into a side chip unless the director explicitly marks `exit_intentional`.

## Screenshot and Evidence Acting

Evidence is an actor with a performance:

1. Establish: show enough of the page/app/table that the viewer knows what it is.
2. Focus: push, crop, magnify, cursor, scan line, red box, or bracket on the exact detail.
3. Label: attach a short text label to the detail, not floating unrelated text.
4. Hold: keep it readable after the narration mentions it.
5. Store or exit: shrink to evidence stack, slide away, or match-cut into the next asset.

Never use a screenshot only as a background texture when it is supposed to prove a claim.
