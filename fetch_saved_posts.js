/**
 * Instagram Saved Posts Exporter
 *
 * Run this in the browser console while logged into instagram.com.
 * It fetches all your saved posts via the web API and downloads them as JSON.
 *
 * Usage:
 *   1. Go to instagram.com and log in
 *   2. Open DevTools (F12) → Console
 *   3. Paste this entire script and press Enter
 *   4. Wait for it to finish (progress is logged to console)
 *   5. A JSON file will download automatically
 */

(async function exportSavedPosts() {
  const csrftoken = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith("csrftoken="))
    ?.split("=")[1];

  if (!csrftoken) {
    console.error("No CSRF token found. Are you logged into Instagram?");
    return;
  }

  const headers = {
    "X-CSRFToken": csrftoken,
    "X-Requested-With": "XMLHttpRequest",
    "X-IG-App-ID": "936619743392459",
  };

  const allPosts = [];
  let hasMore = true;
  let maxId = "";
  let page = 0;

  console.log("Fetching saved posts...");

  while (hasMore) {
    const url = maxId
      ? `/api/v1/feed/saved/posts/?max_id=${maxId}`
      : "/api/v1/feed/saved/posts/";

    const resp = await fetch(url, { headers, credentials: "include" });
    const data = await resp.json();

    const items = data.items || [];
    for (const item of items) {
      const media = item.media;
      if (!media) continue;

      const post = {
        pk: String(media.pk),
        code: media.code,
        username: media.user?.username || "",
        full_name: media.user?.full_name || "",
        taken_at: media.taken_at,
        caption_text: media.caption?.text || "",
        thumbnail_url:
          media.image_versions2?.candidates?.[0]?.url ||
          media.carousel_media?.[0]?.image_versions2?.candidates?.[0]?.url ||
          "",
      };
      allPosts.push(post);
    }

    page++;
    console.log(`Page ${page}: ${items.length} items (${allPosts.length} total)`);

    hasMore = data.more_available === true;
    maxId = data.next_max_id || "";

    // Small delay to avoid rate limiting
    await new Promise((r) => setTimeout(r, 500));
  }

  console.log(`Done! ${allPosts.length} posts fetched. Downloading JSON...`);

  // Download as JSON file
  const blob = new Blob([JSON.stringify(allPosts, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "instagram_saved_posts.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
})();
