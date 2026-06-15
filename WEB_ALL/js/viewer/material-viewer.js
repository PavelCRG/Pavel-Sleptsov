/**
 * Просмотр HTML-работ внутри портала — без iframe для страницы целиком.
 * Ваш HTML/JS/CSS не меняются: подгружаются как есть, пути и скрипты чинит только просмотрщик.
 */
(function () {
    var scopeApi = window.MaterialViewerScope;
    if (!scopeApi) {
        return;
    }

    var SCOPE = scopeApi.SCOPE;
    var contentEl = document.getElementById("material-content");
    var loadingEl = document.getElementById("material-loading");
    var titleEl = document.getElementById("material-viewer-title");
    var openNew = document.getElementById("material-open-new");
    var placeholderEl = document.getElementById("material-placeholder");
    var viewer = document.querySelector(".material-viewer");
    var barEl = document.querySelector(".material-viewer__bar");

    if (!contentEl) {
        return;
    }

    var links = document.querySelectorAll(".lab-catalog [data-material-src]");
    var currentBase = null;
    var currentSrc = null;
    var currentActiveLink = null;
    var mediaObserver = null;
    var catalogEl = document.querySelector(".lab-layout__catalog");
    var mobileMq = window.matchMedia("(max-width: 900px)");
    var backBtn = null;

    function isHtmlSrc(src) {
        return /\.html?(\?|#|$)/i.test(src) || /\.html?$/i.test(src.split("/").pop() || "");
    }

    function isPdfSrc(src) {
        return /\.pdf(\?|#|$)/i.test(src);
    }

    function isAssetSrc(src) {
        return /\.(jpe?g|png|gif|webp|svg|mp3|mp4|wav|zip|rar|docx?|css|js)(\?|#|$)/i.test(src);
    }

    function isSpecialHref(href) {
        return (
            href.indexOf("mailto:") === 0 ||
            href.indexOf("tel:") === 0 ||
            href.indexOf("skype:") === 0 ||
            href.indexOf("javascript:") === 0
        );
    }

    function pathKey(url) {
        try {
            return new URL(url, window.location.href).pathname.replace(/\/+$/, "");
        } catch (e) {
            return url;
        }
    }

    function fileName(url) {
        var key = pathKey(url);
        var parts = key.split("/");
        return parts[parts.length - 1] || key;
    }

    function fixBrokenLocalPath(url) {
        if (!url || (url.indexOf(":\\") === -1 && !/^[a-zA-Z]:[\\/]/.test(url))) {
            return url;
        }
        var parts = url.replace(/\\/g, "/").split("/");
        var file = parts.pop();
        var parent = (parts.pop() || "").toLowerCase();
        if (parent === "images" || parent === "image") {
            return "images/" + file;
        }
        return file;
    }

    function isRelativeResource(url) {
        if (!url) {
            return false;
        }
        if (/^(data:|blob:|https?:)/i.test(url) || url.indexOf("//") === 0) {
            return false;
        }
        return true;
    }

    function resolveMediaUrl(url, base) {
        if (!url || /^data:/i.test(url) || /^blob:/i.test(url)) {
            return url;
        }

        if (isRelativeResource(url)) {
            return scopeApi.resolveUrl(fixBrokenLocalPath(url), base);
        }

        try {
            var resolved = new URL(url, window.location.href);
            var baseUrl = new URL(base, window.location.href);
            if (resolved.pathname.indexOf(baseUrl.pathname.replace(/\/$/, "")) === 0) {
                return url;
            }
            var file = resolved.pathname.split("/").pop() || url.split("/").pop();
            if (file) {
                return scopeApi.resolveUrl(fixBrokenLocalPath(file), base);
            }
        } catch (e) { /* ignore */ }

        return url;
    }

    function disconnectMediaObserver() {
        if (mediaObserver) {
            mediaObserver.disconnect();
            mediaObserver = null;
        }
    }

    function patchMediaUrls(root, base) {
        root.querySelectorAll("img[src], video[src], audio[src], source[src], input[src]").forEach(function (el) {
            var src = el.getAttribute("src");
            if (!src) {
                return;
            }
            var fixed = resolveMediaUrl(src, base);
            if (fixed !== src) {
                el.setAttribute("src", fixed);
            }
        });

        root.querySelectorAll("[srcset]").forEach(function (el) {
            var srcset = el.getAttribute("srcset");
            if (!srcset) {
                return;
            }
            var fixed = srcset.split(",").map(function (part) {
                part = part.trim();
                var pieces = part.split(/\s+/);
                if (isRelativeResource(pieces[0])) {
                    pieces[0] = resolveMediaUrl(pieces[0], base);
                }
                return pieces.join(" ");
            }).join(", ");
            if (fixed !== srcset) {
                el.setAttribute("srcset", fixed);
            }
        });

        root.querySelectorAll("[background]").forEach(function (el) {
            var bg = el.getAttribute("background");
            if (!bg) {
                return;
            }
            var fixed = resolveMediaUrl(bg, base);
            if (fixed !== bg) {
                el.setAttribute("background", fixed);
            }
        });
    }

    function watchMediaUrls(root, base) {
        disconnectMediaObserver();
        mediaObserver = new MutationObserver(function (mutations) {
            mutations.forEach(function (m) {
                if (m.type !== "attributes" || !root.contains(m.target)) {
                    return;
                }
                if (m.attributeName === "src") {
                    var src = m.target.getAttribute("src");
                    if (!src) {
                        return;
                    }
                    var fixed = resolveMediaUrl(src, base);
                    if (fixed !== src) {
                        m.target.setAttribute("src", fixed);
                    }
                    return;
                }
                if (m.attributeName === "srcset") {
                    var srcset = m.target.getAttribute("srcset");
                    if (!srcset) {
                        return;
                    }
                    var fixed = srcset.split(",").map(function (part) {
                        part = part.trim();
                        var pieces = part.split(/\s+/);
                        if (isRelativeResource(pieces[0])) {
                            pieces[0] = resolveMediaUrl(pieces[0], base);
                        }
                        return pieces.join(" ");
                    }).join(", ");
                    if (fixed !== srcset) {
                        m.target.setAttribute("srcset", fixed);
                    }
                }
            });
        });
        mediaObserver.observe(root, {
            attributes: true,
            subtree: true,
            attributeFilter: ["src", "srcset"]
        });
    }

    function setStandaloneLink(src) {
        if (!openNew || !src) {
            return;
        }
        openNew.href = scopeApi.resolveUrl(src, window.location.href);
        openNew.target = "_blank";
        openNew.rel = "noopener noreferrer";
        openNew.hidden = false;
    }

    function setPlaceholderVisible(show) {
        if (placeholderEl) {
            placeholderEl.hidden = !show;
        }
    }

    function setBarVisible(visible, label) {
        if (barEl) {
            barEl.classList.toggle("is-visible", visible);
        }
        if (titleEl) {
            titleEl.textContent = label || "";
        }
        if (!visible && openNew) {
            openNew.hidden = true;
        }
    }

    function setActiveLink(active) {
        currentActiveLink = active || null;
        links.forEach(function (a) {
            a.classList.toggle("is-active", a === active);
        });
        updateBackButton();
    }

    function getOpenLabGroup() {
        if (currentActiveLink) {
            var fromLink = currentActiveLink.closest(".lab-group");
            if (fromLink) {
                return fromLink;
            }
        }
        var activeInCatalog = document.querySelector(".lab-catalog .lab-files a.is-active");
        if (activeInCatalog) {
            return activeInCatalog.closest(".lab-group");
        }
        return document.querySelector(".lab-catalog .lab-group[open]");
    }

    function updateBackButton() {
        if (!backBtn) {
            return;
        }
        var hasContent = contentEl && contentEl.classList.contains("is-active");
        var group = getOpenLabGroup();
        var show = mobileMq.matches && hasContent && !!group;
        backBtn.hidden = !show;
        if (show) {
            var nameEl = group.querySelector(".lab-group__name");
            backBtn.textContent = nameEl
                ? "↑ " + nameEl.textContent.trim()
                : "↑ К условию";
        }
    }

    function scrollToCatalogGroup() {
        var group = getOpenLabGroup();
        if (!group || !catalogEl) {
            return;
        }

        if (!group.open) {
            group.open = true;
        }

        var header = document.querySelector(".site-header");
        var headerH = header ? header.offsetHeight : 0;
        var catalogTop = catalogEl.getBoundingClientRect().top + window.scrollY - headerH - 10;

        window.scrollTo({ top: Math.max(0, catalogTop), behavior: "smooth" });

        window.setTimeout(function () {
            var groupTop = group.offsetTop - catalogEl.offsetTop;
            catalogEl.scrollTo({
                top: Math.max(0, groupTop - 8),
                behavior: "smooth"
            });
            group.classList.add("lab-group--flash");
            window.setTimeout(function () {
                group.classList.remove("lab-group--flash");
            }, 1400);
        }, 380);
    }

    function openParentDetails(el) {
        var node = el;
        while (node && node !== document.body) {
            if (node.tagName === "DETAILS" && !node.open) {
                node.open = true;
            }
            node = node.parentElement;
        }
    }

    function findNamedFrame(root, name) {
        if (!name || /^_(blank|self|parent|top)$/i.test(name)) {
            return null;
        }
        return root.querySelector('iframe[name="' + name + '"], frame[name="' + name + '"]');
    }

    function cleanupBrokenTargets(root) {
        root.querySelectorAll("a[target], area[target]").forEach(function (el) {
            var name = el.getAttribute("target");
            if (!findNamedFrame(root, name)) {
                el.removeAttribute("target");
            }
        });
    }

    function fixRelativeUrls(root, base) {
        patchMediaUrls(root, base);

        root.querySelectorAll("a[href], area[href]").forEach(function (el) {
            var href = el.getAttribute("href");
            if (href && href.indexOf("#") !== 0 && !isSpecialHref(href) && isRelativeResource(href)) {
                el.setAttribute("href", scopeApi.resolveUrl(href, base));
            }
        });
    }

    function appendScopedStyle(cssText, cssBase) {
        if (!cssText || !cssText.trim()) {
            return;
        }
        var rewritten = scopeApi.rewriteCssUrls(cssText, cssBase);
        var el = document.createElement("style");
        el.textContent = scopeApi.scopeCss(rewritten);
        contentEl.appendChild(el);
    }

    function runAllScripts(doc, wrap, base) {
        var scriptNodes = doc.querySelectorAll("script");
        wrap.querySelectorAll("script").forEach(function (node) {
            node.remove();
        });

        var writeSink = document.createElement("div");
        writeSink.className = "material-viewer__write-target";
        wrap.appendChild(writeSink);

        var originalWrite = document.write;
        var originalWriteln = document.writeln;

        function enableWriteRedirect() {
            document.write = function (html) {
                if (html == null) {
                    return;
                }
                writeSink.insertAdjacentHTML("beforeend", String(html));
            };
            document.writeln = function (html) {
                document.write(String(html) + "\n");
            };
        }

        function disableWriteRedirect() {
            document.write = originalWrite;
            document.writeln = originalWriteln;
        }

        var index = 0;

        function runNext() {
            if (index >= scriptNodes.length) {
                disableWriteRedirect();
                fixRelativeUrls(writeSink, base);
                return Promise.resolve();
            }

            var oldScript = scriptNodes[index];
            index += 1;

            return new Promise(function (resolve) {
                enableWriteRedirect();
                var script = document.createElement("script");
                Array.prototype.slice.call(oldScript.attributes).forEach(function (attr) {
                    if (attr.name === "src") {
                        script.setAttribute("src", scopeApi.resolveUrl(attr.value, base));
                    } else {
                        script.setAttribute(attr.name, attr.value);
                    }
                });

                var externalSrc = oldScript.getAttribute("src");
                if (externalSrc) {
                    script.onload = function () {
                        disableWriteRedirect();
                        resolve();
                    };
                    script.onerror = function () {
                        disableWriteRedirect();
                        resolve();
                    };
                }

                script.textContent = externalSrc ? "" : oldScript.textContent;
                wrap.appendChild(script);

                if (!externalSrc) {
                    disableWriteRedirect();
                    resolve();
                }
            }).then(runNext);
        }

        return runNext();
    }

    function showLoading(show) {
        if (loadingEl) {
            loadingEl.hidden = !show;
        }
    }

    function clearContent() {
        disconnectMediaObserver();
        contentEl.innerHTML = "";
        contentEl.hidden = true;
        contentEl.classList.remove("is-active");
        setPlaceholderVisible(true);
        updateBackButton();
    }

    function runBodyInit(doc) {
        var body = doc && doc.body;
        if (!body) {
            return;
        }

        var onloadAttr = body.getAttribute("onload") || body.getAttribute("onLoad");
        if (!onloadAttr) {
            return;
        }

        try {
            (new Function(onloadAttr))();
        } catch (e) { /* onload в атрибуте body */ }
    }

    function injectHtml(html, base, doc) {
        if (!doc) {
            doc = new DOMParser().parseFromString(html, "text/html");
        }

        var overviewArticle = doc.querySelector("article.day-overview");
        if (overviewArticle) {
            var overviewDoc = new DOMParser().parseFromString(
                "<!DOCTYPE html><html><head></head><body></body></html>",
                "text/html"
            );
            doc.querySelectorAll('head link[rel="stylesheet"], head style').forEach(function (node) {
                overviewDoc.head.appendChild(node.cloneNode(true));
            });
            var embedded = overviewArticle.cloneNode(true);
            embedded.classList.add("day-overview--embedded");
            overviewDoc.body.appendChild(embedded);
            doc = overviewDoc;
        }

        clearContent();
        currentBase = base;

        var baseEl = doc.querySelector("base[href]");
        var documentBase = baseEl ? scopeApi.resolveUrl(baseEl.getAttribute("href"), base) : base;
        var stylePromises = [];

        doc.querySelectorAll("style").forEach(function (style) {
            appendScopedStyle(style.textContent, documentBase);
        });

        doc.querySelectorAll('link[rel="stylesheet"]').forEach(function (link) {
            var href = scopeApi.resolveUrl(link.getAttribute("href"), documentBase);
            stylePromises.push(
                fetch(href)
                    .then(function (response) {
                        if (!response.ok) {
                            throw new Error("HTTP " + response.status);
                        }
                        return response.text();
                    })
                    .then(function (cssText) {
                        appendScopedStyle(cssText, href);
                    })
                    .catch(function () { /* внешний CSS недоступен */ })
            );
        });

        var wrap = document.createElement("div");
        wrap.className = SCOPE;

        if (doc.body.getAttribute("style")) {
            wrap.setAttribute("style", doc.body.getAttribute("style"));
        }
        if (doc.body.className) {
            wrap.className += " " + doc.body.className;
        }

        wrap.innerHTML = doc.body.innerHTML;
        fixRelativeUrls(wrap, documentBase);
        cleanupBrokenTargets(wrap);
        contentEl.appendChild(wrap);

        return Promise.all(stylePromises).then(function () {
            return runAllScripts(doc, wrap, documentBase);
        }).then(function () {
            runBodyInit(doc);
            patchMediaUrls(wrap, documentBase);
            watchMediaUrls(wrap, documentBase);
            setPlaceholderVisible(false);
            contentEl.hidden = false;
            contentEl.classList.add("is-active");
            updateBackButton();
        });
    }

    function showError(src, message) {
        var resolved = scopeApi.resolveUrl(src, window.location.href);
        clearContent();
        currentBase = null;
        setStandaloneLink(resolved);
        setPlaceholderVisible(false);
        currentSrc = null;
        var err = document.createElement("p");
        err.className = "material-viewer__error";
        err.textContent = message || "Не удалось загрузить материал.";
        contentEl.appendChild(err);
        var link = document.createElement("a");
        link.href = resolved;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Открыть в новой вкладке";
        contentEl.appendChild(document.createElement("br"));
        contentEl.appendChild(link);
        contentEl.hidden = false;
        contentEl.classList.add("is-active");
        updateBackButton();
    }

    function findCatalogLink(src) {
        var srcKey = pathKey(src);
        var srcFile = fileName(src);
        var found = null;

        links.forEach(function (a) {
            var dataSrc = a.getAttribute("data-material-src") || "";
            var resolved = scopeApi.resolveUrl(dataSrc, window.location.href);
            if (pathKey(resolved) === srcKey || fileName(resolved) === srcFile) {
                found = a;
            }
        });

        return found;
    }

    function updateHash(src) {
        try {
            var key = pathKey(scopeApi.resolveUrl(src, window.location.href));
            history.replaceState(null, "", "#" + encodeURIComponent(key.replace(/^\//, "")));
        } catch (e) { /* ignore */ }
    }

    function openWork(src, label, linkEl) {
        if (!isHtmlSrc(src)) {
            return;
        }

        var resolvedSrc = scopeApi.resolveUrl(src, window.location.href);
        currentSrc = resolvedSrc;

        setBarVisible(true, label || fileName(resolvedSrc));
        var isOverview = /\/overviews\//i.test(resolvedSrc);
        if (isOverview) {
            if (openNew) {
                openNew.hidden = true;
            }
        } else {
            setStandaloneLink(resolvedSrc);
        }

        var activeLink = linkEl || findCatalogLink(resolvedSrc) || null;

        setActiveLink(activeLink);
        if (activeLink) {
            openParentDetails(activeLink);
        }
        updateHash(resolvedSrc);

        if (viewer && viewer.scrollIntoView) {
            var isMobile = window.matchMedia("(max-width: 900px)").matches;
            viewer.scrollIntoView({ behavior: "smooth", block: isMobile ? "start" : "nearest" });
        }

        var base = scopeApi.baseUrlFrom(resolvedSrc);

        showLoading(true);
        clearContent();
        setPlaceholderVisible(false);

        fetch(resolvedSrc)
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }
                return response.text();
            })
            .then(function (html) {
                return injectHtml(html, base);
            })
            .then(function () {
                showLoading(false);
            })
            .catch(function () {
                showLoading(false);
                showError(resolvedSrc, "Не удалось загрузить файл. Проверьте, что сайт открыт через веб-сервер (не file://).");
            });
    }

    function navigateInjectedLink(linkNode, href) {
        var path = href;
        var hash = "";
        var hashIndex = href.indexOf("#");
        if (hashIndex !== -1) {
            path = href.slice(0, hashIndex);
            hash = href.slice(hashIndex);
        }

        if (!path) {
            return;
        }

        if (isPdfSrc(path)) {
            window.open(path, "_blank", "noopener,noreferrer");
            return;
        }

        if (!isHtmlSrc(path)) {
            return;
        }

        var resolved = scopeApi.resolveUrl(path, currentBase || window.location.href);
        var catalogLink = findCatalogLink(resolved);
        var linkLabel = (linkNode.getAttribute("title") || linkNode.getAttribute("alt") || linkNode.textContent || "").trim();
        if (!linkLabel) {
            linkLabel = fileName(resolved);
        }
        openWork(resolved, linkLabel, catalogLink);

        if (hash) {
            window.setTimeout(function () {
                var target = contentEl.querySelector(hash);
                if (target && target.scrollIntoView) {
                    target.scrollIntoView({ behavior: "smooth", block: "nearest" });
                }
            }, 150);
        }
    }

    function handleInjectedLinkClick(e) {
        var linkNode = e.target.closest("a, area");
        if (!linkNode || !contentEl.contains(linkNode)) {
            return;
        }

        var href = linkNode.getAttribute("href");
        if (!href) {
            if (linkNode.tagName === "A") {
                e.preventDefault();
            }
            return;
        }

        if (isSpecialHref(href)) {
            return;
        }

        if (href === "#") {
            e.preventDefault();
            return;
        }

        if (href.indexOf("#") === 0 && href.length > 1) {
            return;
        }

        var targetName = linkNode.getAttribute("target");
        var wrap = contentEl.querySelector("." + SCOPE);
        if (targetName && wrap && findNamedFrame(wrap, targetName)) {
            return;
        }

        var path = href;
        var hashIndex = href.indexOf("#");
        if (hashIndex !== -1) {
            path = href.slice(0, hashIndex);
        }

        if (!path) {
            return;
        }

        if (isPdfSrc(path) || isAssetSrc(path)) {
            e.preventDefault();
            window.open(scopeApi.resolveUrl(path, currentBase || window.location.href), "_blank", "noopener,noreferrer");
            return;
        }

        if (!isHtmlSrc(path)) {
            return;
        }

        e.preventDefault();
        navigateInjectedLink(linkNode, href);
    }

    function handleInjectedFormSubmit(e) {
        var form = e.target;
        if (!form || form.tagName !== "FORM" || !contentEl.contains(form)) {
            return;
        }
        e.preventDefault();
    }

    links.forEach(function (a) {
        a.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            openWork(a.getAttribute("data-material-src"), a.textContent.trim(), a);
        });
    });

    contentEl.addEventListener("click", handleInjectedLinkClick);
    contentEl.addEventListener("submit", handleInjectedFormSubmit);

    function openFromHash() {
        var hash = location.hash.replace(/^#/, "");
        if (!hash) {
            return;
        }
        if (/\.pdf(\?|#|$)/i.test(hash)) {
            return;
        }
        var path = decodeURIComponent(hash);
        var found = null;

        links.forEach(function (a) {
            var dataSrc = a.getAttribute("data-material-src") || "";
            var resolved = scopeApi.resolveUrl(dataSrc, window.location.href);
            if (pathKey(resolved) === pathKey(path) || pathKey(resolved).indexOf(path) !== -1 || path.indexOf(pathKey(resolved)) !== -1) {
                found = a;
            }
        });

        if (found) {
            openWork(found.getAttribute("data-material-src"), found.textContent.trim(), found);
        }
    }

    setBarVisible(false, "");
    openFromHash();
    window.addEventListener("hashchange", openFromHash);

    if (catalogEl && barEl) {
        backBtn = document.createElement("button");
        backBtn.type = "button";
        backBtn.className = "material-viewer__back-catalog";
        backBtn.hidden = true;
        backBtn.setAttribute("aria-label", "Вернуться к условию в списке");
        backBtn.addEventListener("click", scrollToCatalogGroup);
        barEl.insertBefore(backBtn, barEl.firstChild);
        mobileMq.addEventListener("change", updateBackButton);
    }
})();
