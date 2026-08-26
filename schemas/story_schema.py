from flask import abort


# ── Serializers ───────────────────────────────────────────────────────────────

def serialize_story_media(media_item):
    """Convert a StoryMedia ORM object to a plain dict."""
    return {
        "id": media_item.id,
        "story_id": media_item.story_id,
        "media_url": media_item.media_url,
        "created_at": media_item.created_at.isoformat(),
    }


def serialize_story(story, include_org=False, include_media=True):
    """Convert a Story ORM object to a plain dict."""
    data = {
        "id": story.id,
        "organization_id": story.organization_id,
        "title": story.title,
        "content": story.content,
        "featured": story.featured,
        "published": story.published,
        "created_at": story.created_at.isoformat(),
        "updated_at": story.updated_at.isoformat(),
    }

    if include_media:
        data["media"] = [serialize_story_media(m) for m in story.media]

    if include_org and story.organization:
        data["organization"] = {
            "id": story.organization.id,
            "name": story.organization.name,
        }

    return data


# ── Validators ────────────────────────────────────────────────────────────────

def validate_create_story(data: dict) -> dict:
    """
    Validate payload for creating a story.
    Returns clean dict. Calls abort(400) on failure.
    """
    errors = []

    # Required: organization_id
    org_id = data.get("organization_id")
    if org_id is None:
        errors.append("'organization_id' is required.")
    else:
        try:
            org_id = int(org_id)
            if org_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append("'organization_id' must be a positive integer.")

    # Required: title
    title = (data.get("title") or "").strip()
    if not title:
        errors.append("'title' is required.")
    elif len(title) > 250:
        errors.append("'title' must be 250 characters or fewer.")

    # Required: content
    content = (data.get("content") or "").strip()
    if not content:
        errors.append("'content' is required.")

    # Optional: media_urls (list of URL strings)
    media_urls = data.get("media_urls", [])
    if not isinstance(media_urls, list):
        errors.append("'media_urls' must be a list of URL strings.")
    else:
        for url in media_urls:
            if not isinstance(url, str) or not url.strip():
                errors.append("Each item in 'media_urls' must be a non-empty string.")
                break

    if errors:
        abort(400, description="; ".join(errors))

    return {
        "organization_id": org_id,
        "title": title,
        "content": content,
        "featured": bool(data.get("featured", False)),
        "published": bool(data.get("published", False)),
        "media_urls": [u.strip() for u in media_urls if u.strip()],
    }


def validate_update_story(data: dict) -> dict:
    """
    Validate payload for updating a story.
    All fields optional. Calls abort(400) on failure.
    """
    errors = []
    cleaned = {}

    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            errors.append("'title' cannot be empty.")
        elif len(title) > 250:
            errors.append("'title' must be 250 characters or fewer.")
        else:
            cleaned["title"] = title

    if "content" in data:
        content = (data["content"] or "").strip()
        if not content:
            errors.append("'content' cannot be empty.")
        else:
            cleaned["content"] = content

    if "featured" in data:
        if not isinstance(data["featured"], bool):
            errors.append("'featured' must be a boolean.")
        else:
            cleaned["featured"] = data["featured"]

    if "published" in data:
        if not isinstance(data["published"], bool):
            errors.append("'published' must be a boolean.")
        else:
            cleaned["published"] = data["published"]

    if not cleaned and not errors:
        abort(400, description="No valid fields provided for update.")

    if errors:
        abort(400, description="; ".join(errors))

    return cleaned


def validate_add_media(data: dict) -> list:
    """
    Validate a list of media URLs to add to a story.
    Returns a clean list of URL strings.
    """
    media_urls = data.get("media_urls")
    if not media_urls or not isinstance(media_urls, list):
        abort(400, description="'media_urls' must be a non-empty list of URL strings.")

    cleaned = [u.strip() for u in media_urls if isinstance(u, str) and u.strip()]
    if not cleaned:
        abort(400, description="'media_urls' must contain at least one valid URL string.")

    return cleaned
