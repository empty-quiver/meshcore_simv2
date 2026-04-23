# MeshCore Stock Firmware: Dynamic Topology Failure Analysis

Generated from source audit of `/Users/sigxcpu/MeshCore` (firmware v1.15.0, April 2026).

---

## 1. Path Caching: Structure and Location

**Where stored:** `ContactInfo.out_path[]` / `ContactInfo.out_path_len`

Each contact has a single embedded path slot:

```c
// src/helpers/ContactInfo.h:8-31
struct ContactInfo {
  ...
  uint8_t out_path_len;      // 0xFF = OUT_PATH_UNKNOWN (no path)
  uint8_t out_path[MAX_PATH_SIZE];  // MAX_PATH_SIZE = 64 bytes
  ...
};
```

**Sentinel value:** `OUT_PATH_UNKNOWN = 0xFF` (`src/helpers/ContactInfo.h:6`).
When `out_path_len == OUT_PATH_UNKNOWN`, the node sends flood instead of direct.

**Capacity:** One path per contact (not a list). No secondary paths stored.
`MAX_CONTACTS = 32` (default, overridden to 100 in companion_radio `MyMesh.h:59`).
Total path storage is `MAX_CONTACTS × 64 bytes` = at most ~6 KB for 100 contacts.

**Structure:** The path is a byte string of 1–3 byte repeater pub_key hashes
(the hash size is embedded in the top 2 bits of `path_len`; lower 6 bits are the hop count).
Path is stored as received in a `PAYLOAD_TYPE_PATH` packet.

**No global routing table.** The path is per-contact, stored inline in the contact struct.

---

## 2. Cache Entry Lifetime: When Is a Path Overwritten or Invalidated?

**Overwritten unconditionally on any new inbound PATH packet:**

```c
// src/helpers/BaseChatMesh.cpp:304-321
bool BaseChatMesh::onContactPathRecv(ContactInfo& from, ..., uint8_t* out_path, uint8_t out_path_len, ...) {
  // NOTE: default impl, we just replace the current 'out_path' regardless,
  // whenever sender sends us a new out_path.
  // FUTURE: could store multiple out_paths per contact, and try to find which is the 'best'(?)
  from.out_path_len = mesh::Packet::copyPath(from.out_path, out_path, out_path_len);
  from.lastmod = getRTCClock()->getCurrentTime();
  onContactPathUpdated(from);
  ...
}
```

**No TTL, no age-out.** There is zero timer-based cache invalidation. A path entry lives in RAM
(and is persisted to flash) indefinitely until:

- A new `PAYLOAD_TYPE_PATH` packet arrives for that contact (overwrites unconditionally).
- The user/app issues `CMD_RESET_PATH` (`companion_radio/MyMesh.cpp:1242-1252`):
  ```c
  recipient->out_path_len = OUT_PATH_UNKNOWN;
  ```
- The contact slot is evicted when `MAX_CONTACTS` is full and
  `shouldOverwriteWhenFull()` returns true — evicts by oldest `lastmod` timestamp
  (`BaseChatMesh.cpp:70-90`).

**No LRU on paths; no penalty; no probabilistic jitter.** Path quality is never scored.
"First path wins" for a given flood wave:

```c
// src/Mesh.cpp:136-138 (comment in onRecvPacket())
// NOTE: this is a 'first packet wins' impl. When receiving from multiple paths,
// the first to arrive wins. For flood mode, the path may not be the 'best'
// in terms of hops.
```

---

## 3. ACK-Timeout Handling: What Happens on Send Failure?

### ACK timeout trigger

`BaseChatMesh` maintains a single `txt_send_timeout` deadline (`BaseChatMesh.h:65`).
It is set by `sendMessage()` or `sendCommandData()` immediately after queuing the packet:

```c
// src/helpers/BaseChatMesh.cpp:418-435
int BaseChatMesh::sendMessage(...) {
  ...
  if (recipient.out_path_len == OUT_PATH_UNKNOWN) {
    sendFloodScoped(recipient, pkt);
    txt_send_timeout = futureMillis(est_timeout = calcFloodTimeoutMillisFor(t));
  } else {
    sendDirect(pkt, recipient.out_path, recipient.out_path_len);
    txt_send_timeout = futureMillis(est_timeout = calcDirectTimeoutMillisFor(t, recipient.out_path_len));
  }
}
```

### Timeout formulas (companion_radio/MyMesh.cpp:102-106, 834-842)

```c
#define SEND_TIMEOUT_BASE_MILLIS        500
#define FLOOD_SEND_TIMEOUT_FACTOR       16.0f
#define DIRECT_SEND_PERHOP_FACTOR       6.0f
#define DIRECT_SEND_PERHOP_EXTRA_MILLIS 250

uint32_t calcFloodTimeoutMillisFor(uint32_t pkt_airtime_ms) {
  return 500 + (16.0 * pkt_airtime_ms);
}

uint32_t calcDirectTimeoutMillisFor(uint32_t pkt_airtime_ms, uint8_t path_len) {
  uint8_t hops = path_len & 63;   // lower 6 bits = hop count
  return 500 + ((pkt_airtime_ms * 6.0 + 250) * (hops + 1));
}
```

**Typical LoRa SF10/BW250 airtime** for a ~60-byte message packet is approximately 700 ms
(from RadioLib `getTimeOnAir()` backed by chip calculation).

- **Flood timeout:** `500 + 16×700 ≈ 11,700 ms ≈ 11.7 s`
- **Direct, 1-hop path:** `500 + (700×6+250)×2 = 500 + 4450×2 ≈ 9,400 ms ≈ 9.4 s`
- **Direct, 2-hop path (2 repeaters):** `500 + (700×6+250)×3 ≈ 13,850 ms ≈ 13.9 s`

### Timeout callback — `onSendTimeout()`

In companion_radio this is a no-op:

```c
// companion_radio/MyMesh.cpp:844
void MyMesh::onSendTimeout() {}
```

The timeout fires once in `BaseChatMesh::loop()` (`BaseChatMesh.cpp:934-937`) and clears the timer.
**The firmware itself does not retry.** Retries are entirely the responsibility of the
client application (the MeshCore app), which re-calls `CMD_SEND_TXT_MSG` with an
incremented `attempt` byte. The `attempt` field changes the packet hash (preventing
dedup rejection), but the firmware does not increment it automatically.

### No "suspend this path" / penalty logic in stock firmware

There is no concept equivalent to BGP route dampening or TopoGraph's path penalty.
The only related mechanism is `handleReturnPathRetry()` (`BaseChatMesh.cpp:336-341`):

```c
// called when we still have a cached out_path but the OTHER end is still flooding:
void BaseChatMesh::handleReturnPathRetry(const ContactInfo& contact, ...) {
  // re-send a reciprocal return path to sender (DIRECTLY), 3 second delay
  sendDirect(rpath, contact.out_path, contact.out_path_len, 3000);
}
```

This is a path-resync helper, not a penalty. It triggers on ACK-received-via-flood
while `out_path_len != OUT_PATH_UNKNOWN`.

---

## 4. Flood Rediscovery: When Does a Fresh Flood Happen?

**Conditions for flood send (from `sendMessage()`, `BaseChatMesh.cpp:425-428`):**

```c
if (recipient.out_path_len == OUT_PATH_UNKNOWN) {
  sendFloodScoped(recipient, pkt);   // FLOOD
} else {
  sendDirect(pkt, recipient.out_path, recipient.out_path_len);  // DIRECT
}
```

Binary decision: flood iff `out_path_len == 0xFF`. No gradual degradation,
no retry-count-triggered re-flood.

**After an ack-timeout, there is no automatic path reset or re-flood in firmware.**
The path entry is NOT cleared on timeout. The app must either:
- Accept failure and retry (which uses the same stale path again), or
- Call `CMD_RESET_PATH` to set `out_path_len = OUT_PATH_UNKNOWN`, which causes the next
  send to flood.

Some app implementations do call `CMD_RESET_PATH` after N timeouts; this is client-side
policy, not firmware-enforced. From firmware's perspective, there is no "this cache entry
failed N times, re-flood" path.

---

## 5. Path Learning: How Does the Recipient Record the Reverse Path?

When alice sends a flood TXT_MSG to bob, bob receives the flood packet with
alice's hops accumulated in `packet->path[]`. Bob then calls:

```c
// BaseChatMesh.cpp:224-228
if (packet->isRouteFlood()) {
  mesh::Packet* path = createPathReturn(from.id, secret, packet->path, packet->path_len,
                                        PAYLOAD_TYPE_ACK, (uint8_t *)&ack_hash, 4);
  if (path) sendFloodScoped(from, path, TXT_ACK_DELAY);
}
```

The `createPathReturn()` encodes the **inbound flood path** (alice→repeaters→bob) as the
reverse route. This PATH packet is flooded back, and when alice receives it:

```c
// Mesh.cpp:162-168 (inside onRecvPacket(), PAYLOAD_TYPE_PATH handling)
if (onPeerPathRecv(pkt, j, secret, path, path_len, ...)) {
  if (pkt->isRouteFlood()) {
    // send a reciprocal return path to sender, but send DIRECTLY!
    mesh::Packet* rpath = createPathReturn(&src_hash, secret, pkt->path, pkt->path_len, 0, NULL, 0);
    if (rpath) sendDirect(rpath, path, path_len, 500);
  }
}
```

Alice stores the reverse path from bob → `contact.out_path`. Bob (on the return trip)
also gains alice's path.

**The path is purely derived from packet->path[] (repeaters stamping their pub_key hash
as they forward).** There is no broadcast snooping or out-of-band measurement.
The first flood packet to arrive wins (first-path-wins semantics, as noted in the comment
at `Mesh.cpp:136`).

---

## 6. Timescales: Numeric Values

| Event | Value | Source |
|---|---|---|
| `TXT_ACK_DELAY` (ACK send delay at receiver) | 200 ms | `BaseChatMesh.cpp:9` |
| `SERVER_RESPONSE_DELAY` (server reply delay) | 300 ms | `BaseChatMesh.cpp:6` |
| Flood timeout (SF10/BW250, 60-byte msg) | ~11,700 ms (~11.7 s) | `MyMesh.cpp:102-106,834` |
| Direct timeout, 1-hop (SF10/BW250) | ~9,400 ms (~9.4 s) | `MyMesh.cpp:837-841` |
| Direct timeout, 2-hop (SF10/BW250) | ~13,900 ms (~13.9 s) | same |
| Retry count (firmware) | **0 — firmware never retries** | `MyMesh.cpp:844` |
| Retry count (app layer, typical MeshCore app) | 3 retries (attempts 0..3) | `BaseChatMesh.cpp:396-415` |
| Cache entry implicit TTL | **None — never expires** | `ContactInfo.h`, `onContactPathRecv` |
| Time between app-layer retries | Est. 1× timeout per attempt | app policy, not firmware |
| Max total wait before app gives up (3 retries, 1-hop) | ~3 × 9.4 s = ~28 s | derived |
| Max total wait before app gives up (3 retries, flood) | ~3 × 11.7 s = ~35 s | derived |
| Repeater local advert interval (default) | 2 min (`advert_interval=1` × 2×60s) | `simple_repeater/MyMesh.cpp:886,1022` |
| Repeater flood advert interval (default) | 12 hours | `simple_repeater/MyMesh.cpp:887,1029` |
| Packet dedup table size (seen hashes) | 128 entries (cyclic, no TTL) | `SimpleMeshTables.h:9` |

**On typical SF10/BW250 LoRa:** RadioLib's `getTimeOnAir()` for a 60-byte payload
(~80 bytes on-wire including path) returns ~700 ms.
For SF12/BW125 (common long-range configs), airtime is ~3,500 ms, giving:
- Flood timeout: ~56,500 ms (~56 s)
- Direct 1-hop timeout: ~22,500 ms (~22 s)

**No inter-message cooldown in firmware** prevents sending to a dead path repeatedly.
The only throttle is the duty-cycle budget (`getAirtimeBudgetFactor()`, default 1.0 =
50% duty cycle over a 1-hour window).

---

## 7. Dynamic Topology Implications: The Failing-Bridge Scenario

**Setup:** Alice → Repeater-R → Bob. R silently disappears.

**What baseline does NOT detect:**
- It does not monitor SNR of the path.
- It does not probe the path with keepalives (keepalives are only used for Room Server
  "connections", not peer-to-peer chat, `BaseChatMesh.cpp:662-777`).
- It does not age out the path entry.

**Failure sequence per message:**

1. Alice sends MSG via direct path through R.
2. The packet is transmitted into the void (R is gone).
3. After `~9-14 seconds` (direct timeout), `onSendTimeout()` fires.
4. Firmware does **nothing**: `onSendTimeout() {}`.
5. App layer receives RESP_CODE_SENT but no PUSH_CODE_SEND_CONFIRMED.
6. App retries (attempt=1) with the **same stale path** (still cached).
7. Same failure, same ~9-14 s timeout.
8. App retries (attempt=2, attempt=3) similarly.

**Messages lost per failure cycle:** Typically **3 messages** (attempts 0, 1, 2) if app
uses 3 retries, plus the original = 3-4 user-perceived failures, each costing ~9-14 s.

**Total wall-clock time before the app "gives up" on a given message:** ~28–42 s
(3 retries × 9-14 s timeout each), depending on path length and radio params.

**Recovery — how baseline recovers:**

Recovery only happens when one of these occurs:
a. **App calls `CMD_RESET_PATH`** (manually or after N failures). Next send floods,
   and if any path exists through another repeater, the flood succeeds and a new
   `PAYLOAD_TYPE_PATH` arrives, updating `out_path`. Recovery in ~1 flood timeout.

b. **Bob sends a message to Alice first** (or any other action that causes
   `createPathReturn()` to run) — this pushes a new PATH packet to alice, which
   overwrites the stale cached path.

c. **An advertisement from Bob arrives** — this does NOT update `out_path` directly.
   Adverts update `last_advert_timestamp` and `lastmod` but not `out_path`.
   `onAdvertRecv()` (`BaseChatMesh.cpp:106-179`) does not touch `out_path_len`.

**Number of flood packets on recovery:** One flood send of the message (once path is
reset to UNKNOWN), which is forwarded by every repeater in range (each copies and
retransmits with a random jitter delay). In a 3-hop network with branching, expect
~5-15 flood copies on-air.

---

## Timeline of a Dying-Bridge Event (Stock Firmware)

**Scenario:** SF10/BW250, 1 repeater (R) in the path, app doing 3 retries before giving up,
advert interval = 2 min.

```
t=0       Repeater R goes out of range (silently — no NACK, no notification).

t=0s      Alice sends MSG-1 (attempt=0) direct via cached R path.
          Firmware: sendDirect(), sets 9.4 s timeout.

t=9.4s    Timeout fires. onSendTimeout() = no-op.
          App: no PUSH_CODE_SEND_CONFIRMED received.
          App: retries MSG-1 (attempt=1) direct via SAME stale R path.
          New 9.4 s timeout set.

t=18.8s   Timeout again. App: retries MSG-1 (attempt=2).

t=28.2s   Timeout again. App: gives up on MSG-1 (3 attempts exhausted).
          App shows "Send failed." to user.
          Path is STILL cached as via R (firmware never cleared it).

          USER ACTION REQUIRED: user or app calls CMD_RESET_PATH.
          out_path_len set to OUT_PATH_UNKNOWN.

t=28.2s+  Alice sends MSG-2 (attempt=0) as FLOOD (path now unknown).
          Flood timeout = ~11.7 s.
          If an alternative path exists (or direct), the flood finds Bob.
          Bob's receiver calls createPathReturn(), floods back a PATH packet.

t≈28.8s   Alice receives PATH packet from Bob via new route.
          onContactPathRecv() overwrites out_path with new path.
          txt_send_timeout cleared (ACK embedded in PATH packet).

t≈29s+    Alice's path to Bob is now repaired. Subsequent messages use new path.

--- WITHOUT CMD_RESET_PATH (worst case: app keeps retrying same stale path) ---

Each user message: 3 retries × 9.4 s = 28.2 s of spinning before "failed."
Path remains stale indefinitely. ALL messages fail until:
  - App calls CMD_RESET_PATH, OR
  - Bob sends something first, OR
  - Radio is power-cycled (in-RAM path survives restart if persisted to flash).

Total recovery window (with app reset): ~30 s from last attempt to new path established.
Total recovery window (without reset): INFINITE — baseline has no self-healing path expiry.

--- FLOOD PACKET COUNT ON RECOVERY ---
1 flood send of the message.
Each repeater in range re-floods with jitter (see routeRecvPacket(), Mesh.cpp:328-341).
In a 3-node linear chain with 1 surviving repeater: ~3-4 retransmits on-air.
In a mesh with 3 repeaters, each forwarding once: ~7-10 retransmits (hop-count bounded
by allowPacketForward() flood_max, default 64 — effectively unlimited for small meshes).
```

---

## Summary for A/B Test Design

| Parameter | Baseline Value |
|---|---|
| Path cache size | 1 path per contact, never expires |
| Path invalidation | Manual only (`CMD_RESET_PATH`) or contact eviction |
| ACK timeout (1-hop direct, SF10/BW250) | ~9.4 s |
| ACK timeout (flood, SF10/BW250) | ~11.7 s |
| Firmware retry count | 0 (app-layer retries, typically 3) |
| Total app give-up time per message | ~28–35 s (3 retries, SF10) |
| Self-healing after bridge failure | None — path never cleared automatically |
| SNR-based path penalization | None |
| Time to recover with app reset | ~30–45 s (1 flood cycle + new PATH exchange) |
| Time to recover WITHOUT app reset | Indefinite (manual intervention required) |

**Sim design implication:** A meaningful A/B test window should be at least **300 s (5 min)**
to capture 2-3 full failure+recovery cycles. Measurement should begin counting from t=0
(node disappears) and track: (a) first failed message, (b) first successful message after
recovery, (c) total messages lost in window. Baseline recovery latency is dominated by
the app-retry policy (~30 s), not the radio physics (~10 s ACK timeout).
TopoGraph's path penalty/decay should be compared against this ~30 s baseline window.
