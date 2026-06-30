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

## Screenshot and Evidence Acting

Evidence is an actor with a performance:

1. Establish: show enough of the page/app/table that the viewer knows what it is.
2. Focus: push, crop, magnify, cursor, scan line, red box, or bracket on the exact detail.
3. Label: attach a short text label to the detail, not floating unrelated text.
4. Hold: keep it readable after the narration mentions it.
5. Store or exit: shrink to evidence stack, slide away, or match-cut into the next asset.

Never use a screenshot only as a background texture when it is supposed to prove a claim.
