///usr/bin/env jbang "$0" "$@" ; exit $?
//JAVA 25
//DEPS com.fasterxml.jackson.core:jackson-databind:2.18.3

import module java.base;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

/**
 * Generate HTML detail pages from JSON snippet files and slug-template.html.
 * JBang equivalent of generate.py — produces identical output.
 *
 * Uses modern Java features up to Java 25:
 *   - Compact source file / void main()  (JEP 512)
 *   - Module imports                      (JEP 511)
 *   - Records                             (JEP 395)
 *   - Sealed interfaces                   (JEP 409)
 *   - Pattern matching for switch         (JEP 441)
 *   - Text blocks                         (JEP 378)
 *   - Unnamed variables (_)               (JEP 456)
 *   - Stream.toList()                     (JDK 16)
 *   - String.formatted()                  (JDK 15)
 *   - SequencedMap                        (JDK 21)
 */

static final String BASE_URL = "https://javaevolved.github.io";
static final String TEMPLATE_FILE = "slug-template.html";
static final Pattern TOKEN_PATTERN = Pattern.compile("\\{\\{(\\w+)}}");
static final ObjectMapper MAPPER = new ObjectMapper();

static final List<String> CATEGORIES = List.of(
        "language", "collections", "strings", "streams", "concurrency",
        "io", "errors", "datetime", "security", "tooling");

static final Map<String, String> CATEGORY_DISPLAY = Map.ofEntries(
        Map.entry("language", "Language"),
        Map.entry("collections", "Collections"),
        Map.entry("strings", "Strings"),
        Map.entry("streams", "Streams"),
        Map.entry("concurrency", "Concurrency"),
        Map.entry("io", "I/O"),
        Map.entry("errors", "Errors"),
        Map.entry("datetime", "Date/Time"),
        Map.entry("security", "Security"),
        Map.entry("tooling", "Tooling"));

static final Set<String> EXCLUDED_KEYS = Set.of("_path", "prev", "next", "related");

// -- Records for structured data -----------------------------------------

record Snippet(JsonNode node) {
    String get(String field) { return node.get(field).asText(); }
    String slug()       { return get("slug"); }
    String category()   { return get("category"); }
    String title()      { return get("title"); }
    String summary()    { return get("summary"); }
    String difficulty()  { return get("difficulty"); }
    String jdkVersion() { return get("jdkVersion"); }
    String oldLabel()   { return get("oldLabel"); }
    String modernLabel(){ return get("modernLabel"); }
    String oldCode()    { return get("oldCode"); }
    String modernCode() { return get("modernCode"); }
    String oldApproach(){ return get("oldApproach"); }
    String modernApproach() { return get("modernApproach"); }
    String explanation(){ return get("explanation"); }
    String support()    { return get("support"); }
    String key()        { return "%s/%s".formatted(category(), slug()); }
    String catDisplay() { return CATEGORY_DISPLAY.get(category()); }

    Optional<String> prev() {
        return node.has("prev") && !node.get("prev").isNull()
                ? Optional.of(node.get("prev").asText()) : Optional.empty();
    }

    Optional<String> next() {
        return node.has("next") && !node.get("next").isNull()
                ? Optional.of(node.get("next").asText()) : Optional.empty();
    }

    List<String> related() {
        var rel = node.get("related");
        if (rel == null) return List.of();
        List<String> paths = new ArrayList<>();
        rel.forEach(n -> paths.add(n.asText()));
        return paths;
    }

    JsonNode whyModernWins() { return node.get("whyModernWins"); }
}

// -- Sealed interface for nav arrow rendering ----------------------------

sealed interface NavArrow {
    record Link(String href) implements NavArrow {}
    record Disabled()        implements NavArrow {}
    record Empty()           implements NavArrow {}
}

// -- Entry point (compact source file, JEP 512) -------------------------

void main() throws IOException {
    var template = Files.readString(Path.of(TEMPLATE_FILE));
    var allSnippets = loadAllSnippets();
    IO.println("Loaded %d snippets".formatted(allSnippets.size()));

    // Generate HTML files
    for (var snippet : allSnippets.values()) {
        var html = generateHtml(template, snippet, allSnippets).strip();
        Files.writeString(Path.of(snippet.category(), snippet.slug() + ".html"), html);
    }
    IO.println("Generated %d HTML files".formatted(allSnippets.size()));

    // Rebuild data/snippets.json
    var snippetsList = allSnippets.values().stream()
            .map(s -> {
                Map<String, Object> map = MAPPER.convertValue(s.node(),
                        new TypeReference<LinkedHashMap<String, Object>>() {});
                EXCLUDED_KEYS.forEach(map::remove);
                return map;
            })
            .toList();

    Files.createDirectories(Path.of("data"));
    var prettyMapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
    Files.writeString(Path.of("data", "snippets.json"),
            prettyMapper.writeValueAsString(snippetsList) + "\n");
    IO.println("Rebuilt data/snippets.json with %d entries".formatted(snippetsList.size()));

    // Patch index.html with the current snippet count
    int count = allSnippets.size();
    var indexContent = Files.readString(Path.of("index.html"))
            .replace("{{snippetCount}}", String.valueOf(count));
    Files.writeString(Path.of("index.html"), indexContent);
    IO.println("Patched index.html with snippet count: %d".formatted(count));
}

// -- Loading snippets ----------------------------------------------------

SequencedMap<String, Snippet> loadAllSnippets() throws IOException {
    SequencedMap<String, Snippet> snippets = new LinkedHashMap<>();
    for (var cat : CATEGORIES) {
        var catDir = Path.of(cat);
        if (!Files.isDirectory(catDir)) continue;

        try (var stream = Files.newDirectoryStream(catDir, "*.json")) {
            var sorted = new ArrayList<Path>();
            stream.forEach(sorted::add);
            sorted.sort(Path::compareTo);

            for (var path : sorted) {
                var snippet = new Snippet(MAPPER.readTree(path.toFile()));
                snippets.put(snippet.key(), snippet);
            }
        }
    }
    return snippets;
}

// -- HTML escaping -------------------------------------------------------

String escape(String text) {
    return switch (text) {
        case null -> "";
        case String s -> s.replace("&", "&amp;")
                          .replace("<", "&lt;")
                          .replace(">", "&gt;")
                          .replace("\"", "&quot;")
                          .replace("'", "&#x27;");
    };
}

String jsonEscape(String text) {
    try {
        var quoted = MAPPER.writeValueAsString(text);
        var inner = quoted.substring(1, quoted.length() - 1);
        var sb = new StringBuilder(inner.length());
        for (int i = 0; i < inner.length(); i++) {
            char c = inner.charAt(i);
            if (c > 127) {
                sb.append("\\u%04x".formatted((int) c));
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    } catch (IOException _) {
        throw new RuntimeException("Failed to JSON-escape: " + text);
    }
}

String urlEncode(String s) {
    return URLEncoder.encode(s, StandardCharsets.UTF_8).replace("+", "%20");
}

// -- Rendering helpers ---------------------------------------------------

String renderNavArrows(Snippet snippet) {
    NavArrow prev = snippet.prev()
            .<NavArrow>map(p -> new NavArrow.Link("/" + p + ".html"))
            .orElse(new NavArrow.Disabled());
    NavArrow next = snippet.next()
            .<NavArrow>map(n -> new NavArrow.Link("/" + n + ".html"))
            .orElse(new NavArrow.Empty());

    return renderArrow(prev, "Previous pattern", "←")
            + "\n          "
            + renderArrow(next, "Next pattern", "→");
}

String renderArrow(NavArrow arrow, String label, String symbol) {
    return switch (arrow) {
        case NavArrow.Link(var href) ->
                "<a href=\"%s\" aria-label=\"%s\">%s</a>".formatted(href, label, symbol);
        case NavArrow.Disabled() ->
                "<span class=\"nav-arrow-disabled\">%s</span>".formatted(symbol);
        case NavArrow.Empty() -> "";
    };
}

String renderWhyCards(JsonNode whyList) {
    var cards = new ArrayList<String>();
    for (var w : whyList) {
        cards.add("""
                <div class="why-card">
                  <div class="why-icon">%s</div>
                  <h3>%s</h3>
                  <p>%s</p>
                </div>\
        """.formatted(
                w.get("icon").asText(),
                escape(w.get("title").asText()),
                escape(w.get("desc").asText())).stripTrailing());
    }
    return String.join("\n", cards);
}

String renderRelatedCard(Snippet rel) {
    return """
                <a href="/%s/%s.html" class="tip-card">
                  <div class="tip-card-body">
                    <div class="tip-card-header">
                      <div class="tip-badges">
                        <span class="badge %s">%s</span>
                        <span class="badge %s">%s</span>
                      </div>
                    </div>
                    <h3>%s</h3>
                  </div>
                  <div class="card-code">
                    <div class="card-code-layer old-layer">
                      <div class="mini-label">%s</div>
                      <pre class="code-text">%s</pre>
                    </div>
                    <div class="card-code-layer modern-layer">
                      <div class="mini-label">%s</div>
                      <pre class="code-text">%s</pre>
                    </div>
                    <span class="hover-hint">Hover to see modern ➜</span>
                  </div>
                  <div class="tip-card-footer">
                    <span class="browser-support"><span class="dot"></span>JDK %s+</span>
                    <span class="arrow-link">→</span>
                  </div>
                </a>\
        """.formatted(
            rel.category(), rel.slug(),
            rel.category(), rel.catDisplay(),
            rel.difficulty(), rel.difficulty(),
            escape(rel.title()),
            escape(rel.oldLabel()), escape(rel.oldCode()),
            escape(rel.modernLabel()), escape(rel.modernCode()),
            rel.jdkVersion()).stripTrailing();
}

String renderRelatedSection(Snippet snippet, Map<String, Snippet> allSnippets) {
    return snippet.related().stream()
            .filter(allSnippets::containsKey)
            .map(path -> renderRelatedCard(allSnippets.get(path)))
            .collect(Collectors.joining("\n"));
}

String renderSocialShare(String slug, String title) {
    var pageUrl = "%s/%s.html".formatted(BASE_URL, slug);
    var shareText = "%s \u2013 java.evolved".formatted(title);
    var encodedUrl = urlEncode(pageUrl);
    var encodedText = urlEncode(shareText);

    return """
              <div class="social-share">
                <span class="share-label">Share</span>
                <a href="https://x.com/intent/tweet?url=%s&text=%s" target="_blank" rel="noopener" class="share-btn share-x" aria-label="Share on X">𝕏</a>
                <a href="https://bsky.app/intent/compose?text=%s%%20%s" target="_blank" rel="noopener" class="share-btn share-bsky" aria-label="Share on Bluesky">🦋</a>
                <a href="https://www.linkedin.com/sharing/share-offsite/?url=%s" target="_blank" rel="noopener" class="share-btn share-li" aria-label="Share on LinkedIn">in</a>
                <a href="https://www.reddit.com/submit?url=%s&title=%s" target="_blank" rel="noopener" class="share-btn share-reddit" aria-label="Share on Reddit">⬡</a>
              </div>\
            """.formatted(
            encodedUrl, encodedText,
            encodedText, encodedUrl,
            encodedUrl,
            encodedUrl, encodedText).stripTrailing();
}

// -- Main generation logic -----------------------------------------------

String generateHtml(String template, Snippet snippet, Map<String, Snippet> allSnippets) {
    var replacements = Map.ofEntries(
            Map.entry("title",              escape(snippet.title())),
            Map.entry("summary",            escape(snippet.summary())),
            Map.entry("slug",               snippet.slug()),
            Map.entry("category",           snippet.category()),
            Map.entry("categoryDisplay",    snippet.catDisplay()),
            Map.entry("difficulty",         snippet.difficulty()),
            Map.entry("jdkVersion",         snippet.jdkVersion()),
            Map.entry("oldLabel",           escape(snippet.oldLabel())),
            Map.entry("modernLabel",        escape(snippet.modernLabel())),
            Map.entry("oldCode",            escape(snippet.oldCode())),
            Map.entry("modernCode",         escape(snippet.modernCode())),
            Map.entry("oldApproach",        escape(snippet.oldApproach())),
            Map.entry("modernApproach",     escape(snippet.modernApproach())),
            Map.entry("explanation",        escape(snippet.explanation())),
            Map.entry("support",            escape(snippet.support())),
            Map.entry("canonicalUrl",       "%s/%s/%s.html".formatted(BASE_URL, snippet.category(), snippet.slug())),
            Map.entry("flatUrl",            "%s/%s.html".formatted(BASE_URL, snippet.slug())),
            Map.entry("titleJson",          jsonEscape(snippet.title())),
            Map.entry("summaryJson",        jsonEscape(snippet.summary())),
            Map.entry("categoryDisplayJson", jsonEscape(snippet.catDisplay())),
            Map.entry("navArrows",          renderNavArrows(snippet)),
            Map.entry("whyCards",           renderWhyCards(snippet.whyModernWins())),
            Map.entry("relatedCards",       renderRelatedSection(snippet, allSnippets)),
            Map.entry("socialShare",        renderSocialShare(snippet.slug(), snippet.title()))
    );

    var m = TOKEN_PATTERN.matcher(template);
    var sb = new StringBuilder();
    while (m.find()) {
        var key = m.group(1);
        m.appendReplacement(sb, Matcher.quoteReplacement(
                replacements.getOrDefault(key, m.group(0))));
    }
    m.appendTail(sb);
    return sb.toString();
}
