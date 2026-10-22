---
name: aws-kinesis-stream-no-consumers
scope: aws
service: AWS Kinesis Data Streams
waste_category: idle
confidence: likely
---

# AWS Kinesis Stream with Producers but No Consumers

## Problem

A Kinesis Data Stream bills on the write side whether or not anything reads
it. In provisioned mode the meters are shard-hours and PUT payload units; in
on-demand Standard mode they are a per-stream hourly charge plus GB written;
extended and long-term retention add a per-shard-hour or per-GB-month line on
top. None of those meters needs a consumer. So a stream whose consumer was
decommissioned, whose Lambda event source mapping was disabled, or whose
Firehose delivery stream was deleted keeps costing the full producer-side
amount while delivering nothing. The pattern hides because the producer
still works: writes succeed, dashboards show throughput, and no alarm fires.
In one 140-account estate about 30% of Kinesis producers were found to have
no consumer (Seshadri Reddy Kommepalli, Equifax, FinOps X 2026; an
illustration, not a benchmark).

## Symptoms

- `IncomingRecords` is steadily above zero while `GetRecords.Records` and
  `SubscribeToShardEvent.Records` are zero over the whole lookback window
- `describe-stream-summary` reports `ConsumerCount: 0`, and no Lambda event
  source mapping or Firehose delivery stream names the stream as its source
- The stream was created for a project, pipeline or analytics job that has
  since been retired, and the producer side (an application, an IoT fleet, a
  CloudWatch Logs subscription filter) was never told
- Provisioned streams keep a shard count sized for a consumer that no longer
  exists; on-demand streams keep paying the per-stream hour

## Detection

Stream-level metrics in the `AWS/Kinesis` namespace are published every
minute at no charge, so the check needs no enhanced monitoring. Run it per
region. The script uses GNU `date`; it was written from the API reference,
so run it on one region and read the output before trusting it across an
estate.

```bash
# Streams with writes but no reads over the last 14 days (one region)
START=$(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ)
END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
for s in $(aws kinesis list-streams --query 'StreamNames[]' --output text); do
  total() {
    aws cloudwatch get-metric-statistics --namespace AWS/Kinesis \
      --metric-name "$1" --dimensions Name=StreamName,Value="$s" \
      --start-time "$START" --end-time "$END" --period 1209600 --statistics Sum \
      --query 'Datapoints[0].Sum' --output text | sed 's/None/0/'
  }
  in=$(total IncomingRecords)
  get=$(total GetRecords.Records)
  sub=$(total SubscribeToShardEvent.Records)
  consumers=$(aws kinesis describe-stream-summary --stream-name "$s" \
    --query 'StreamDescriptionSummary.ConsumerCount' --output text)
  if [[ "${in%.*}" -gt 0 && "${get%.*}" -eq 0 && "${sub%.*}" -eq 0 ]]; then
    echo "NO CONSUMER: $s  incoming_records=$in  registered_consumers=$consumers"
  fi
done
```

`SubscribeToShardEvent.*` metrics carry a `ConsumerName` dimension and are
emitted only while an enhanced fan-out subscription is active, so a stream
with registered consumers but no live subscription also reads zero there;
`ConsumerCount` tells the two apart. A `None` datapoint on `IncomingRecords`
means nothing was written in the window either: the stream is then orphaned
rather than idle, and the same fix applies.

```sql
-- Athena over CUR 2.0: Kinesis spend by stream, to rank the API-detected list
SELECT
  line_item_resource_id           AS stream_arn,
  line_item_usage_account_id      AS account,
  line_item_usage_type            AS usage_type,
  SUM(line_item_usage_amount)     AS units_30d,
  SUM(line_item_unblended_cost)   AS cost_30d
FROM cur2
WHERE line_item_usage_start_date >= current_date - interval '30' day
  AND product_servicecode = 'AmazonKinesis'
GROUP BY 1, 2, 3
ORDER BY cost_30d DESC;
```

## Fix

1. Confirm there is no consumer the metrics cannot see: a Lambda event source
   mapping (`aws lambda list-event-source-mappings`, filtered on the stream
   ARN), a Firehose delivery stream with the stream as source, a Managed
   Service for Apache Flink application, or a cross-account consumer reading
   through a resource policy. All of these read through `GetRecords` or
   `SubscribeToShard`, so zero on both metrics is strong evidence, not proof.
2. Stop the producer first where you can, and watch for breakage for one
   retention period. A producer nobody owns is the cheaper thing to switch
   off, and the stream then drains on its own.
3. Delete the stream. If retention beyond 24 hours was enabled and the data
   might matter, export it first; the records go with the stream.
4. For streams that must stay (a compliance feed read once a quarter), size
   a provisioned stream to the smallest shard count the write rate needs, or
   move it to on-demand if writes are low and bursty, and tag the stream with
   the consumer that justifies it.
5. Prevent recurrence: require a `consumer` or `owner` tag at creation, and
   alert when `GetRecords.Records` plus `SubscribeToShardEvent.Records` stays
   at zero for 7 days on a stream whose `IncomingRecords` does not.

## Anti-pattern

- Deciding from application logs. The producer's logs show successful
  writes, which is the signal that misleads; the read-side metrics and the
  consumer inventory are the source of truth.
- Deleting the stream before the producer. The producer then fails loudly,
  and a cross-account consumer you did not find comes back as an incident
  instead of a saving.
- Treating a registered enhanced fan-out consumer as proof of use. A
  registration without an active subscription reads nothing;
  `SubscribeToShardEvent.Records` is the signal, `ConsumerCount` the context.

## See also

- `references/finops-waste-detection-playbooks.md` - "idle" category rubric
  and the "alert first, delete next" shape for automated clean-up
- `playbooks/aws-idle-load-balancer.md` - the same idle-resource pattern on
  another hourly-billed service
- `references/finops-aws-billing.md` - billing data foundations behind the CUR query
- Billing units: https://aws.amazon.com/kinesis/data-streams/pricing/; metric
  names: https://docs.aws.amazon.com/streams/latest/dev/monitoring-with-cloudwatch.html
  (both read 14 October 2026). The no-consumer billing consequence follows
  from the units; the pricing page does not state it in those words.

---

> *Cloud FinOps Playbook by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*
