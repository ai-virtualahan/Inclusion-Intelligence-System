(function () {
  const WRAPPER_SELECTOR = ".table-wrapper, .questions-table-wrapper, .choices-table-wrapper";
  const scrollbar = document.createElement("div");
  const scrollbarContent = document.createElement("div");
  let activeWrapper = null;
  let syncing = false;
  let updateQueued = false;

  scrollbar.className = "floating-table-scrollbar";
  scrollbar.setAttribute("aria-hidden", "true");
  scrollbarContent.className = "floating-table-scrollbar-content";
  scrollbar.appendChild(scrollbarContent);
  document.body.appendChild(scrollbar);

  function isVisible(element) {
    const style = window.getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
  }

  function findActiveWrapper() {
    const viewportHeight = window.innerHeight;
    const candidates = Array.from(document.querySelectorAll(WRAPPER_SELECTOR))
      .filter(wrapper => {
        const rect = wrapper.getBoundingClientRect();
        const hasHorizontalOverflow = wrapper.scrollWidth > wrapper.clientWidth + 1;
        const crossesViewport = rect.top < viewportHeight - 24 && rect.bottom > 24;
        const nativeScrollbarBelowViewport = rect.bottom > viewportHeight - 8;
        return isVisible(wrapper)
          && hasHorizontalOverflow
          && crossesViewport
          && nativeScrollbarBelowViewport;
      });

    if (!candidates.length) return null;

    return candidates.reduce((best, wrapper) => {
      if (!best) return wrapper;
      const wrapperRect = wrapper.getBoundingClientRect();
      const bestRect = best.getBoundingClientRect();
      return Math.max(wrapperRect.top, 0) >= Math.max(bestRect.top, 0) ? wrapper : best;
    }, null);
  }

  function syncFromWrapper() {
    if (!activeWrapper || syncing) return;
    syncing = true;
    scrollbar.scrollLeft = activeWrapper.scrollLeft;
    syncing = false;
  }

  function setActiveWrapper(wrapper) {
    if (activeWrapper === wrapper) return;

    if (activeWrapper) {
      activeWrapper.removeEventListener("scroll", syncFromWrapper);
    }

    activeWrapper = wrapper;

    if (activeWrapper) {
      activeWrapper.addEventListener("scroll", syncFromWrapper, { passive: true });
    }
  }

  function updateScrollbar() {
    updateQueued = false;
    const wrapper = findActiveWrapper();
    setActiveWrapper(wrapper);

    if (!wrapper) {
      scrollbar.classList.remove("is-visible");
      return;
    }

    const rect = wrapper.getBoundingClientRect();
    const left = Math.max(rect.left, 8);
    const right = Math.min(rect.right, window.innerWidth - 8);

    scrollbar.style.left = `${left}px`;
    scrollbar.style.width = `${Math.max(right - left, 0)}px`;
    scrollbarContent.style.width = `${wrapper.scrollWidth}px`;
    scrollbar.classList.add("is-visible");
    syncFromWrapper();
  }

  function queueUpdate() {
    if (updateQueued) return;
    updateQueued = true;
    window.requestAnimationFrame(updateScrollbar);
  }

  scrollbar.addEventListener("scroll", () => {
    if (!activeWrapper || syncing) return;
    syncing = true;
    activeWrapper.scrollLeft = scrollbar.scrollLeft;
    syncing = false;
  }, { passive: true });

  window.addEventListener("resize", queueUpdate, { passive: true });
  document.addEventListener("scroll", queueUpdate, { passive: true, capture: true });

  if ("ResizeObserver" in window) {
    const resizeObserver = new ResizeObserver(queueUpdate);
    document.querySelectorAll(WRAPPER_SELECTOR).forEach(wrapper => resizeObserver.observe(wrapper));
  }

  if ("MutationObserver" in window) {
    const mutationObserver = new MutationObserver(queueUpdate);
    mutationObserver.observe(document.body, { childList: true, subtree: true });
  }

  queueUpdate();
})();
