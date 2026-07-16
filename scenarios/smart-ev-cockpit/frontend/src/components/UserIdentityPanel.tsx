import { X } from "lucide-react";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { APP_COPY, type UserIdentityPanelLabels } from "../i18n";
import type {
  UpdateUserIdentityRequest,
  UserIdentity,
  UserProfileSummary,
} from "../types/api";

interface UserIdentityPanelProps {
  identity: UserIdentity;
  profile: UserProfileSummary | null;
  actorLabel: string;
  labels?: UserIdentityPanelLabels;
  isSaving: boolean;
  error: string | null;
  onClose: () => void;
  onSave: (payload: UpdateUserIdentityRequest) => Promise<void>;
}

export function UserIdentityPanel({
  identity,
  profile,
  actorLabel,
  labels = APP_COPY.en.identity,
  isSaving,
  error,
  onClose,
  onSave,
}: UserIdentityPanelProps) {
  const [userId, setUserId] = useState(identity.user_id);
  const [displayName, setDisplayName] = useState(identity.display_name);
  const [profileNote, setProfileNote] = useState(identity.profile_note);
  const memoryKindEntries = Object.entries(profile?.memory_kind_counts ?? {});
  const recentMemories = profile?.memories.slice(0, 3) ?? [];
  const userIdText = userId.trim();

  useEffect(() => {
    setUserId(identity.user_id);
    setDisplayName(identity.display_name);
    setProfileNote(identity.profile_note);
  }, [identity]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!userIdText) {
      return;
    }

    await onSave({
      user_id: userIdText,
      display_name: displayName.trim(),
      profile_note: profileNote.trim(),
    });
  }

  return (
    <section
      className="user-identity-panel"
      data-anchor-actor={identity.actor_id}
      role="dialog"
      aria-label={labels.dialogLabel}
    >
      <header className="user-identity-panel__header">
        <div>
          <span>{labels.seat} · {actorLabel}</span>
          <h2>{labels.title}</h2>
          <p>{labels.subtitle}</p>
        </div>
        <button
          type="button"
          className="user-identity-panel__close"
          aria-label={labels.close}
          onClick={onClose}
        >
          <X aria-hidden="true" strokeWidth={1.8} />
        </button>
      </header>

      <form className="user-identity-panel__form" onSubmit={handleSubmit}>
        <label htmlFor="identity-display-name">{labels.displayName}</label>
        <input
          id="identity-display-name"
          type="text"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
        />

        <label htmlFor="identity-user-id">{labels.userId}</label>
        <input
          id="identity-user-id"
          type="text"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          required
        />

        <label htmlFor="identity-profile-note">{labels.profileNote}</label>
        <textarea
          id="identity-profile-note"
          value={profileNote}
          rows={3}
          onChange={(event) => setProfileNote(event.target.value)}
        />

        {error ? (
          <p className="user-identity-panel__error" role="alert">
            {error}
          </p>
        ) : null}

        <button type="submit" disabled={isSaving || !userIdText}>
          {isSaving ? labels.saving : labels.save}
        </button>
      </form>

      <aside className="user-identity-panel__profile" aria-label={labels.profileSummary}>
        <h3>{labels.profileSummary}</h3>
        <p>{profile?.primary_memory ?? labels.noProfile}</p>
        <div>
          <strong>{labels.memoryKinds}</strong>
          {memoryKindEntries.length > 0 ? (
            <ul>
              {memoryKindEntries.map(([kind, count]) => (
                <li key={kind}>{kind} {count}</li>
              ))}
            </ul>
          ) : (
            <span>{labels.noMemoryKinds}</span>
          )}
        </div>
        {recentMemories.length > 0 ? (
          <div>
            <strong>{labels.recentMemories}</strong>
            <ol>
              {recentMemories.map((memory) => (
                <li key={memory.memory_id}>{memory.content}</li>
              ))}
            </ol>
          </div>
        ) : null}
      </aside>
    </section>
  );
}
