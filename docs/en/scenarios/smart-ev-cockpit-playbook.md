# Smart EV Cockpit Workshop Playbook

## Act 1: Build Memory
Presenter action: click Act 1 or send "I usually set 26C and seat heat level 2 in winter."
PowerMem evidence: ADD operation with `memory_kind=cabin_control_preference`.
Vehicle evidence: no state diff is required in this act.
Privacy evidence: raw utterance is not stored as long-term memory.
Talk track: PowerMem stores derived memory, not a raw transcript.
Developer note: inspect metadata fields `actor_id`, `seat_position`, and `source_event_ids`.

## Act 2: Same Utterance, Different People
Presenter action: send "I feel cold." as each actor.
PowerMem evidence: SEARCH filters include actor and seat position.
Vehicle evidence: driver, front passenger, and child produce different safe patches.
Privacy evidence: child voice uses safety policy memory.
Talk track: the same utterance is resolved through person and seat memory.
Developer note: compare selected memory IDs in the evidence drawer.

## Act 3: Cabin Control Routine
Presenter action: send "Use my previous comfort setup."
PowerMem evidence: SEARCH returns `cabin_control_preference` and `driving_preference` memories.
Vehicle evidence: HVAC and seat heat fields show before/after diffs.
Privacy evidence: command history is summarized as a routine, not stored as raw transcript.
Talk track: PowerMem turns repeated actions into procedural memory.
Developer note: inspect `vehicle_action.patch` and selected memory IDs.

## Act 4: Capability Boundary
Presenter action: send "Does this vehicle support rest mode?"
PowerMem evidence: SEARCH returns `vehicle_capability` with unsupported feature metadata.
Vehicle evidence: no vehicle command is executed.
Privacy evidence: the response is based on synthetic vehicle profile only.
Talk track: memory retrieval prevents the assistant from inventing vehicle capabilities.
Developer note: inspect the `memory_kind=vehicle_capability` filter.

## Act 5: Location Recall
Presenter action: send "Take me to the restaurant from last Friday."
PowerMem evidence: SEARCH returns `location_episode` with generalized POI content.
Vehicle evidence: navigation recommendation appears without exact address.
Privacy evidence: exact address and raw place name stay hidden.
Talk track: useful place recall does not require exposing private location details.
Developer note: inspect `visibility=masked` and hidden field reasons.

## Act 6: Media Preference
Presenter action: send "Play something for the child to sleep."
PowerMem evidence: SEARCH returns `media_preference` and `safety_policy`.
Vehicle evidence: media recommendation uses low volume and child-safe content.
Privacy evidence: child identity is represented only as `child_rear_left`.
Talk track: PowerMem combines passenger context and media history.
Developer note: compare actor filters for child versus driver.

## Act 7: Anniversary Recommendation
Presenter action: send "Any plan for tonight?"
PowerMem evidence: SEARCH returns `relationship_event` and safe place preferences.
Vehicle evidence: recommendation card appears without route execution.
Privacy evidence: exact anniversary date is masked in presenter view.
Talk track: personal recommendations can be helpful without revealing sensitive facts.
Developer note: inspect masked metadata in the evidence drawer.

## Act 8: Driving Mode Suggestion
Presenter action: trigger a rainy commute or low SOC context.
PowerMem evidence: SEARCH returns `driving_preference` and `emotional_preference`.
Vehicle evidence: drive mode recommendation appears with SOC context.
Privacy evidence: commute route remains generalized.
Talk track: vehicle state and memory work together for contextual suggestions.
Developer note: inspect vehicle state diff and reason codes.

## Act 9: Proactive Care
Presenter action: trigger low SOC with `POST /events/vehicle`.
PowerMem evidence: SEARCH returns charging reminder tone preference.
Vehicle evidence: SOC and range fields change from normal to low.
Privacy evidence: emotional preference is summarized and not shown as raw complaint.
Talk track: proactive care is useful when tone is personalized and restrained.
Developer note: inspect selected `emotional_preference` memory ID.

## Act 10: Lifecycle And Privacy
Presenter action: jump to Day 90.
PowerMem evidence: `temporary_context` moves to `decayed`; long-term preference stays active.
Vehicle evidence: no direct vehicle command is required.
Privacy evidence: archive and delete actions remain inspectable.
Talk track: lifecycle management keeps memory useful instead of accumulating stale facts.
Developer note: inspect retention score, hit count, and lifecycle status changes.
