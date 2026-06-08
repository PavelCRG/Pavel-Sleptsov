/**
 * Просмотр HTML-работ внутри портала — без iframe.
 * PDF (условия) открываются в новой вкладке из каталога.
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
    var viewer = document.querySelector(".material-viewer");
    var barEl = document.querySelector(".material-viewer__bar");

    if (!contentEl) {
        return;
    }

    var links = document.querySelectorAll('.lab-files a[data-material-src]');
    var currentBase = null;

    function isHtmlSrc(src) {
        return /\.html?(\?|#|$)/i.test(src);
    }

    function isPdfSrc(src) {
        return /\.pdf(\?|#|$)/i.test(src);
    }

    function setBarVisible(visible, label) {
        if (barEl) {
            barEl.classList.toggle("is-visible", visible);
        }
        if (titleEl) {
            titleEl.textContent = label || "";
        }
    }

    function setActiveLink(active) {
        links.forEach(function (a) {
            a.classList.toggle("is-active", a === active);
        });
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

    function fixRelativeUrls(root, base) {
        root.querySelectorAll("[src]").forEach(function (el) {
            var src = el.getAttribute("src");
            if (src) {
                el.setAttribute("src", scopeApi.resolveUrl(src, base));
            }
        });
        root.querySelectorAll("a[href]").forEach(function (el) {
            var href = el.getAttribute("href");
            if (href && href.indexOf("#") !== 0 && href.indexOf("mailto:") !== 0) {
                el.setAttribute("href", scopeApi.resolveUrl(href, base));
            }
        });
    }

    function appendScopedStyle(cssText) {
        if (!cssText || !cssText.trim()) {
            return;
        }
        var el = document.createElement("style");
        el.textContent = scopeApi.scopeCss(cssText);
        contentEl.appendChild(el);
    }

    function runScripts(container, base) {
        container.querySelectorAll("script").forEach(function (oldScript) {
            var script = document.createElement("script");
            Array.prototype.slice.call(oldScript.attributes).forEach(function (attr) {
                if (attr.name === "src") {
                    script.setAttribute("src", scopeApi.resolveUrl(attr.value, base));
                } else {
                    script.setAttribute(attr.name, attr.value);
                }
            });
            if (!oldScript.src) {
                script.textContent = oldScript.textContent;
            }
            oldScript.parentNode.replaceChild(script, oldScript);
        });
    }

    function showLoading(show) {
        if (loadingEl) {
            loadingEl.hidden = !show;
        }
    }

    function clearContent() {
        contentEl.innerHTML = "";
        contentEl.hidden = true;
        contentEl.classList.remove("is-active");
    }

    function injectHtml(html, base) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        clearContent();
        currentBase = base;

        var stylePromises = [];

        doc.querySelectorAll("style").forEach(function (style) {
            appendScopedStyle(style.textContent);
        });

        doc.querySelectorAll('link[rel="stylesheet"]').forEach(function (link) {
            var href = scopeApi.resolveUrl(link.getAttribute("href"), base);
            stylePromises.push(
                fetch(href)
                    .then(function (response) {
                        if (!response.ok) {
                            throw new Error("HTTP " + response.status);
                        }
                        return response.text();
                    })
                    .then(function (cssText) {
                        appendScopedStyle(cssText);
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
        fixRelativeUrls(wrap, base);
        contentEl.appendChild(wrap);

        return Promise.all(stylePromises).then(function () {
            runScripts(wrap, base);
            contentEl.hidden = false;
            contentEl.classList.add("is-active");
        });
    }

    function showError(src, message) {
        clearContent();
        currentBase = null;
        var err = document.createElement("p");
        err.className = "material-viewer__error";
        err.textContent = message || "Не удалось загрузить материал.";
        contentEl.appendChild(err);
        var link = document.createElement("a");
        link.href = src;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = "Открыть в новой вкладке";
        contentEl.appendChild(document.createElement("br"));
        contentEl.appendChild(link);
        contentEl.hidden = false;
        contentEl.classList.add("is-active");
    }

    function findCatalogLink(src) {
        var found = null;
        links.forEach(function (a) {
            var dataSrc = a.getAttribute("data-material-src") || "";
            if (dataSrc === src || scopeApi.resolveUrl(dataSrc, window.location.href) === src) {
                found = a;
            }
        });
        return found;
    }

    function openWork(src, label, linkEl) {
        if (!isHtmlSrc(src)) {
            return;
        }

        setBarVisible(true, label || src.split("/").pop());
        if (openNew) {
            openNew.href = src;
            openNew.hidden = false;
            openNew.onclick = function (ev) {
                ev.preventDefault();
                openWork(src, label || src.split("/").pop(), linkEl || findCatalogLink(src));
            };
        }
        setActiveLink(linkEl || null);
        if (linkEl) {
            openParentDetails(linkEl);
            try {
                history.replaceState(null, "", "#" + encodeURIComponent(src.replace(/^\.\.\//, "")));
            } catch (e) { /* ignore */ }
        }
        if (viewer && viewer.scrollIntoView) {
            viewer.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        var base = scopeApi.baseUrlFrom(src);

        showLoading(true);
        clearContent();

        fetch(src)
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
                showError(src, "Не удалось загрузить файл. Проверьте, что сайт открыт через веб-сервер (не file://).");
            });
    }

    function handleInjectedLinkClick(e) {
        var anchor = e.target.closest("a");
        if (!anchor || !contentEl.contains(anchor)) {
            return;
        }

        var href = anchor.getAttribute("href");
        if (!href) {
            e.preventDefault();
            return;
        }

        if (
            href.indexOf("mailto:") === 0 ||
            href.indexOf("tel:") === 0 ||
            href.indexOf("skype:") === 0 ||
            href.indexOf("javascript:") === 0
        ) {
            return;
        }

        if (href === "#") {
            e.preventDefault();
            return;
        }

        if (href.indexOf("#") === 0 && href.length > 1) {
            return;
        }

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
            anchor.target = "_blank";
            anchor.rel = "noopener noreferrer";
            return;
        }

        if (!isHtmlSrc(path)) {
            return;
        }

        e.preventDefault();

        var resolved = scopeApi.resolveUrl(path, currentBase || window.location.href);
        var catalogLink = findCatalogLink(resolved);
        var linkLabel = anchor.textContent.trim() || resolved.split("/").pop();
        openWork(resolved, linkLabel, catalogLink);

        if (hash) {
            window.setTimeout(function () {
                var target = contentEl.querySelector(hash);
                if (target && target.scrollIntoView) {
                    target.scrollIntoView({ behavior: "smooth", block: "nearest" });
                }
            }, 120);
        }
    }

    links.forEach(function (a) {
        a.addEventListener("click", function (e) {
            e.preventDefault();
            openWork(a.getAttribute("data-material-src"), a.textContent.trim(), a);
        });
    });

    contentEl.addEventListener("click", handleInjectedLinkClick);

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
            var src = a.getAttribute("data-material-src") || "";
            var normalized = src.replace(/^\.\.\//, "");
            if (normalized === path || normalized.indexOf(path) !== -1 || path.indexOf(normalized) !== -1) {
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
})();
