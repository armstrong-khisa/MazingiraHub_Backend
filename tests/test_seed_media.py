from models import Donation, Organization, StoryMedia
from seed import ORGANIZATIONS, STORY_MEDIA, seed


def test_seed_assigns_unsplash_images_to_organizations_and_stories(app):
    with app.app_context():
        seed()

        organizations = Organization.query.all()
        stories_with_media = StoryMedia.query.all()

        assert len(organizations) == len(ORGANIZATIONS)
        assert all(org.image_url.startswith("https://images.unsplash.com/") for org in organizations)
        assert len(stories_with_media) == len(STORY_MEDIA)
        assert all(media.media_url.startswith("https://images.unsplash.com/") for media in stories_with_media)
        assert Donation.query.count() == 10
