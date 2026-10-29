# Requirements and assumptions

Discovery only. No analytics have been implemented. Nothing in this document is a calculated accuracy result.

Checked on 28 October 2026. The repository contained the assignment document and `.cursor/settings.json`. It was not a Git repository. Python 3.12.3, Node.js 22.22.3, and Docker 29.4.3 are installed. No application dependencies or environment files exist.

## Business problem

A UK electricity utility buys power in the day-ahead wholesale market. Wind output is uncertain, so the purchasing team must decide how much other generation to buy before the delivery day, using a wind forecast that already exists at decision time.

The product has to show that forecast and then show how far it was from what actually happened. It must not use a forecast that was published after the decision.

## Official requirements

From `REint Full Stack SWE challenge v4 Shared.docx`:

- National UK wind only, from Elexon. No other data provider.
- Actuals: FUELHH, `fuelType = WIND`. Relevant fields: `startTime`, `generation`. Resolution stated as 30 minutes.
- Forecasts: WINDFOR. Relevant fields: `startTime`, `publishTime`, `generation`.
- Data relevant to purchase decisions made in January 2026.
- Decisions are made one day before the delivery day.
- React frontend, Python backend, Docker, and deployment on Vercel or Heroku.
- Public GitHub repository with an anonymous name.
- README with structure, startup, deployment URL, and AI tools used.
- Unlisted YouTube demo of at most 10 minutes: up to 5 minutes for the customer, up to 5 minutes for the technical review.
- Suggested effort at most 16 hours.
- Official pages: [FUELHH stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) and [WINDFOR stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream).

The assignment does not state the clock time of the purchasing cutoff, the wholesale delivery-day boundary, or how to compare an hourly forecast with a half-hour actual.

## Proposed user workflows

Product name: **Wind Forecast Intelligence**. User: a procurement analyst.

1. Open the overview for the approved January 2026 decision window and see coverage, matched-pair count, MAE, RMSE, and MBE, with the cutoff labelled on screen.
2. Compare the decision-time forecast with actual wind across the delivery intervals. Gaps stay visible.
3. Inspect one delivery interval and see every input used: delivery time, selected forecast, its publication time, the cutoff, the actual, both errors, and include or exclude reason.
4. Read which intervals were dropped and why, including missing actuals, missing eligible forecasts, and forecasts published after the cutoff.

Out of scope: prices, demand, a cost model, other fuels, machine-learning forecasts, accounts, and chat.

## Data sources and fields

Base URL verified by request: `https://data.elexon.co.uk/bmrs/api/v1`. No API key.

| Dataset | Endpoint used | Parameters that returned the requested history | Parameters that were ignored |
|---|---|---|---|
| FUELHH | `GET /datasets/FUELHH/stream` | `settlementDateFrom`, `settlementDateTo`, `fuelType` | `from`, `to` returned the latest periods, not the requested range |
| WINDFOR | `GET /datasets/WINDFOR/stream` | `publishDateTimeFrom`, `publishDateTimeTo` | `from`, `to`, `settlementDateFrom`, `settlementDateTo`, and `startTimeFrom` returned the latest publication only |

The non-stream routes return `{ "data": [ ... ] }`. The stream routes return a JSON array. For the ranges below, one stream response contained the complete result. No page token or `offset` was required. The [Insights developer portal](https://developer.data.elexon.co.uk/) describes stream endpoints as JSON-only and without a stated row limit. That description matches these responses, but the client must still check that the minimum and maximum timestamps cover the request. A wrong parameter does not return an error. It returns the latest snapshot.

FUELHH record fields observed: `dataset`, `publishTime`, `startTime`, `settlementDate`, `settlementPeriod`, `fuelType`, `generation`.

WINDFOR stream record fields observed: `dataset`, `publishTime`, `startTime`, `generation`. The stream records do not include `settlementDate` or `settlementPeriod`.

Timestamps are ISO-8601 UTC with a `Z` suffix, for example `2026-01-11T10:00:00Z`. `generation` was an integer in every row inspected. There were no nulls in the January extracts below.

Units were not printed as a field in the API records. Two official descriptions support MW: the [generation-by-fuel report](https://bmrs.elexon.co.uk/generation-by-fuel-type) says the half-hourly outturn is average MW, and the developer portal describes the latest wind forecast as MW. The endpoint documentation pages themselves did not render, so the unit is not taken from an OpenAPI field description.

The same generation-by-fuel page says this outturn excludes embedded generation and wind farms without operational meters, and that NESO estimated metered wind coverage at about 82% as of 2025. That limitation applies to the outturn report. It has not been verified whether WINDFOR uses exactly the same boundary.

## Confirmed facts versus assumptions

### Confirmed from the API on 28 October 2026

January 2026 data exists.

FUELHH wind for settlement dates 1–31 January 2026:

- One request returned 1,488 rows.
- That is 31 days × 48 half-hours.
- `startTime` runs from `2026-01-01T00:00:00Z` to `2026-01-31T23:30:00Z`.
- Every consecutive gap was 30 minutes. No half-hour was missing.
- `fuelType` was `WIND` on every row. The server-side filter worked. The pipeline will filter again.
- One row per `startTime`. No duplicate actuals in this extract.
- `generation` ranged from 1,695 to 17,805.
- 31 December 2025 and 1 February 2026 also returned 48 half-hours each, from `00:00:00Z` to `23:30:00Z`.
- In this winter month, settlement period 1 starts at 00:00 UTC. A separate WINDFOR evolution record for `2026-01-11T10:00:00Z` was settlement period 21, which is 10:00 if periods begin at midnight. That evolution route is not a source for the product. It was used only to read Elexon's own settlement-period label.

WINDFOR publications with `publishDateTimeFrom=2026-01-01T00:00:00Z` and `publishDateTimeTo=2026-02-01T00:00:00Z`:

- 18,104 rows, about 2.0 MB, in one response.
- 248 publication times, exactly 8 on each calendar day from 1 January through 31 January.
- Usual publication clocks, UTC: 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30.
- Exception: 15 January 2026 has `2026-01-15T12:25:00Z` instead of 11:30. That publication still has 73 hourly rows.
- Every forecast `startTime` is on the hour. Consecutive unique start times are 60 minutes apart. There is no `:30` forecast.
- Each publication covers 73 hourly delivery times. Across January publications, delivery times span `2025-12-31T21:00:00Z` to `2026-02-02T21:00:00Z`.
- No duplicate pair of `startTime` and `publishTime`.
- `generation` ranged from 2,250 to 21,353.
- Publications on 1 January cover delivery hours on 2 January, including 00:00 and 23:00 UTC.
- Publications on 31 January cover delivery hours on 1 February, including 00:00 and 23:00 UTC, and continue through `2026-02-02T21:00:00Z`.

So a next-day delivery interval is inside the forecast horizon at both ends of the month. The first publication of a day is 02:30 UTC, not midnight.

Calling WINDFOR without `publishDateTimeFrom` and `publishDateTimeTo`, or with `from` and `to`, returned only the publication at `2026-10-28T15:30:00Z`. Using those parameters for a January study would analyse the wrong day.

### Not confirmed

- The HTML documentation pages returned an application shell or an error, so parameter lists were confirmed by requests rather than by the rendered OpenAPI page.
- Whether `publishDateTimeTo` is exclusive. Neither bound in the January request equalled an observed publication time.
- Whether FUELHH values are later revised. This extract is one snapshot.
- An official 2026 gate-closure clock time. See the cutoff question below.
- Whether the hourly WINDFOR value is an average MW for the clock hour or the value Elexon attaches only to the settlement period at that timestamp.

### Approved on 28 October 2026

These change the numbers. They are the rules the analysis will implement.

1. Decision dates are the calendar dates 1–31 January 2026 in Europe/London. January 2026 is GMT, so London time and UTC are the same instant. The code still converts explicitly.
2. The delivery period for a decision on date D is the Elexon settlement date D+1, from 00:00 through 23:30 UK time. Delivery dates are therefore 2 January–1 February 2026. The 23:00-to-23:00 wholesale power day is not used.
3. The default cutoff is 09:50 Europe/London on the decision date. It stays configurable and visible. A forecast with `publishTime` equal to the cutoff is eligible. The latest `publishTime` wins. Ties, if any appear, are broken by a deterministic sort and counted. None appeared in the discovery extract.
4. Forecasts and actuals match only when `startTime` is equal. Half-hour actuals at `:30` have no WINDFOR row in this dataset, so they are excluded and counted as missing a forecast. The hourly forecast is not copied onto the following half-hour, and the two half-hours are not averaged.
5. Missing actuals and missing eligible forecasts are excluded. They are not stored as zero.
6. Metrics use `error = forecast_generation - actual_generation` on valid pairs only. Positive mean bias means the forecast was higher than actual.

## Recommended architecture

Local runtime is Docker Compose: a Vite React TypeScript app and a FastAPI service. Business rules live in Python modules, not in route handlers or React components. Tests use fixed records. A separate command calls Elexon.

January 2026 is in the past, and the useful extract is about 2 MB of forecasts plus a few hundred kilobytes of actuals. The API will be called by an explicit refresh command, which writes a raw snapshot and the time it was fetched. The API reads that snapshot. The dashboard does not call Elexon on each click. A refresh replaces the snapshot. This also makes a result reproducible.

Deployment target: Vercel. Current Vercel Functions run Python 3.12+ and FastAPI, and can run an OCI image from `Dockerfile.vercel`. That image is a stateless function, not a long-lived Compose stack. Docker Compose remains the local requirement. The public app should serve the prebuilt snapshot so a request does not depend on Elexon being available. Function response bodies are limited to 4.5 MB, so the API will return the aligned series and summaries, not every historical forecast version. No deployment has been created.

## Important risks

- Silent wrong-day responses. `from` and `to` are accepted and ignored for these stream routes. The loader must reject a snapshot whose time range does not cover the request.
- Hourly forecasts against half-hour actuals. Joining on equal `startTime` leaves every `:30` actual unmatched. Copying the hourly value onto both half-hours would create a forecast Elexon did not publish.
- Look-ahead bias. Any forecast after the cutoff, including later the same day and anything published on the delivery day, must be dropped. WINDFOR keeps publishing through and after delivery. The evolution probe for `2026-01-11T10:00:00Z` had publications from 9 January 02:30 through 11 January 22:30.
- Month edges. "Decisions in January" and "delivery days in January" are different sets. See the questions below.
- Meter coverage. FUELHH wind is not all wind in Britain. Accuracy here is accuracy of this Elexon series, not of total national wind.
- Revisions. A later download can differ from this discovery extract. The app will show the snapshot time.
- The 15 January 12:25 publication shows that publication clocks are not guaranteed. Selection must use `publishTime`, not a fixed list of clock times.
- No prices. The UI can say that a large miss changes how much other power must be bought. It cannot state a saving in pounds.

## Approval record

Answered on 28 October 2026. All four recommended choices were accepted.

| Question | Approved choice |
|---|---|
| Date scope | Decisions 1–31 January 2026. Delivery settlement dates 2 January–1 February 2026. |
| Cutoff | 09:50 Europe/London on the decision day. Publication at the cutoff is eligible. |
| Alignment | Equal `startTime` only. Each `:30` actual is excluded and reported as having no forecast. |
| Day boundary | Elexon settlement day, 00:00–23:30 UK time. |

## Questions requiring approval

Closed. The choices below are kept so the rejected alternatives stay visible. The approved column is in the approval record above.

### 1. Which January dates are in scope?

The assignment says decisions made in January 2026, one day before delivery.

| Choice | Decision dates | Delivery settlement dates |
|---|---|---|
| A. Recommended | 1–31 January 2026 | 2 January–1 February 2026 |
| B | 31 December 2025–30 January 2026 | 1–31 January 2026 |

Choice A follows the sentence in the assignment. Choice B studies generation during January and drops the 1 February delivery that was bought on 31 January. Choice A needs the 1 February actuals, which are available. Choice B needs 31 December forecasts, which were not part of the January publication extract and would be fetched if selected.

### 2. What is the decision cutoff?

No clock time is in the assignment. Nord Pool's GB day-ahead regulations, retrieved as a PDF, say orders must arrive before gate closure and that their day-ahead price calculation starts at 23:00 UK time. The retrieved sections do not state the production gate-closure clock time. Secondary market explainers put the liquid hourly auctions at about 09:20 and 09:50 UK time, and a half-hour auction at about 15:30. Those clock times are not treated as verified.

The cutoff will be a setting, shown in the UI. The default needs approval.

| Choice | Cutoff on decision date D, Europe/London | Latest usual January publication still eligible |
|---|---|---|
| A. Recommended | 09:50 | 09:30. The 11:30 publication is excluded |
| B | 15:30 | 15:30, if the boundary is inclusive |
| C | Another clock time you specify | Depends on the time |

09:50 is recommended because the assignment describes the day-ahead purchase rather than a later intraday adjustment, and because it is after both commonly cited morning hourly auctions. Inclusivity recommended: a forecast published at the cutoff is eligible. In the January extract, normal publication times are `:30`, so 09:50 and 09:30 behave the same. 15:30 inclusive would include the 15:30 publication.

### 3. How should an hourly forecast meet a half-hour actual?

The assignment says 30-minute intervals. The WINDFOR rows for this month are hourly.

| Choice | Comparison | Effect |
|---|---|---|
| A. Recommended | Equal `startTime` only | About half of actuals, the `:30` intervals, have no forecast and are excluded. No invented forecast. |
| B | One pair per clock hour: forecast at `HH:00` against the mean of actuals at `HH:00` and `HH:30` | Uses both actuals. The mean is calculated by us. A hour with only one actual is excluded. |
| C | Copy the hourly forecast onto both half-hours | Doubles the sample with a value Elexon did not publish. Not recommended. |

Choice A is recommended. Elexon's evolution record attached `2026-01-11T10:00:00Z` to one settlement period, not to two. The excluded `:30` intervals will be counted in coverage so the smaller sample is visible.

### 4. Delivery-day clock boundary

Recommended: Elexon settlement dates, midnight to midnight UK time. The alternative, a wholesale day from 23:00 to 23:00, is real market practice but is not how these FUELHH settlement dates are labelled. It will not be used unless you choose it.

## Definition of done

- Approved choices above are the ones implemented, and the screen shows them.
- Source records are FUELHH wind and WINDFOR only, for the approved decision window.
- The selected forecast for every scored interval was published at or before that interval's cutoff.
- Metrics are computed from matched pairs only, with units, pair count, and coverage.
- Tests cover eligibility, latest-forecast selection, duplicate publications, the join, missing values, and the January timezone.
- Docker Compose starts the app locally.
- The Vercel URL is public and has been opened without relying on a local server.
- README, architecture, methodology, deployment notes, and the demo script exist.
- AI tools are named in the README.
- The YouTube script is written. Recording and the submission form remain manual steps.

## Implementation plan

The four business choices are approved. The analysis pipeline, snapshot, and React dashboard are in place. Docker and deployment are still to do.

1. Discovery. This document.
2. Data proof. Save a small real extract and show one real delivery interval under the approved cutoff. Label it as observed data.
3. Backend. Normalise, select, join, calculate, and test. Read the snapshot. Do not hide an Elexon failure with fake rows.
4. Frontend. Overview, forecast-versus-actual chart, error view, one-interval audit, and methodology.
5. Integration. Run the app against the snapshot and check one metric by hand.
6. Docker and Vercel. Verify the deployed health check and one analysis response.
7. README, methodology, architecture, deployment guide, and demo script.
