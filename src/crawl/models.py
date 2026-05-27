from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CrawledDocument:
    id: str
    url: str
    title: str
    technology: str
    category: str
    discovered_at: str
    content_hash: str
    relative_path: str
    output_path: str

    def to_manifest_entry(self, repository: str, sha1: str) -> dict:
        filename = self.relative_path.rsplit("/", 1)[-1]
        return {
            "id": self.id,
            "repository": repository,
            "relative_path": self.relative_path,
            "absolute_path": self.output_path,
            "filename": filename,
            "extension": ".md",
            "size_bytes": 0,
            "sha1": sha1,
            "category": self.category,
            "copied_to": self.output_path,
            "discovered_at": self.discovered_at,
            "url": self.url,
            "title": self.title,
            "technology": self.technology,
            "content_hash": self.content_hash,
        }
