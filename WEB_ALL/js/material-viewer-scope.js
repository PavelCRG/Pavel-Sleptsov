/**
 * Изоляция CSS работ внутри .material-viewer__injected —
 * стили лаб не попадают на портал и наоборот.
 */
(function (global) {
    var SCOPE = "material-viewer__injected";
    var SCOPE_SEL = "." + SCOPE;

    function scopeSelectors(selectors) {
        return selectors.split(",").map(function (sel) {
            sel = sel.trim();
            if (!sel) {
                return sel;
            }
            if (sel === "*") {
                return SCOPE_SEL + " *";
            }
            if (/^html\s*,\s*body$/i.test(sel)) {
                return SCOPE_SEL;
            }
            sel = sel.replace(/^html\s+body/i, SCOPE_SEL);
            sel = sel.replace(/^html\b/i, SCOPE_SEL);
            sel = sel.replace(/^body\b/i, SCOPE_SEL);
            if (sel.indexOf(SCOPE_SEL) === 0) {
                return sel;
            }
            return SCOPE_SEL + " " + sel;
        }).join(", ");
    }

    function scopeCss(cssText) {
        var css = cssText.replace(/\/\*[\s\S]*?\*\//g, "");

        function parseBlock(block) {
            var out = "";
            var i = 0;

            while (i < block.length) {
                var br = block.indexOf("{", i);
                if (br === -1) {
                    break;
                }

                var selectors = block.slice(i, br).trim();
                var depth = 1;
                var j = br + 1;

                while (j < block.length && depth > 0) {
                    if (block[j] === "{") {
                        depth += 1;
                    } else if (block[j] === "}") {
                        depth -= 1;
                    }
                    j += 1;
                }

                var inner = block.slice(br + 1, j - 1);

                if (selectors.charAt(0) === "@") {
                    if (/^@(media|supports|layer|container)\b/i.test(selectors)) {
                        out += selectors + "{" + parseBlock(inner) + "}";
                    } else {
                        out += selectors + "{" + inner + "}";
                    }
                } else {
                    out += scopeSelectors(selectors) + "{" + inner + "}";
                }

                i = j;
            }

            return out;
        }

        return parseBlock(css);
    }

    function resolveUrl(value, base) {
        if (!value || value.indexOf("data:") === 0 || value.indexOf("#") === 0) {
            return value;
        }
        try {
            return new URL(value, base).href;
        } catch (e) {
            return value;
        }
    }

    function rewriteCssUrls(cssText, base) {
        if (!base || !cssText) {
            return cssText;
        }
        return cssText.replace(/url\(\s*(['"]?)([^'")]+?)\1\s*\)/gi, function (match, quote, url) {
            url = url.trim();
            if (/^(data:|https?:|\/\/|#)/i.test(url)) {
                return match;
            }
            return "url(" + quote + resolveUrl(url, base) + quote + ")";
        });
    }

    function baseUrlFrom(src) {
        return new URL("./", new URL(src, window.location.href)).href;
    }

    global.MaterialViewerScope = {
        SCOPE: SCOPE,
        SCOPE_SEL: SCOPE_SEL,
        scopeCss: scopeCss,
        rewriteCssUrls: rewriteCssUrls,
        resolveUrl: resolveUrl,
        baseUrlFrom: baseUrlFrom
    };
})(window);
