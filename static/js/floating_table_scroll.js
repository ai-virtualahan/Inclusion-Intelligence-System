(function () {
  const WRAPPER_SELECTOR = ".table-wrapper, .questions-table-wrapper, .choices-table-wrapper";
  const scrollbar = document.createElement("div");
  const scrollbarTrack = document.createElement("div");
  const scrollbarThumb = document.createElement("div");
  const MIN_THUMB_WIDTH = 48;
  let activeWrapper = null;
  let dragStartX = 0;
  let dragStartScrollLeft = 0;
  let dragging = false;
  let syncing = false;
  let updateQueued = false;

  scrollbar.className = "floating-table-scrollbar";
  scrollbar.setAttribute("aria-label", "Horizontal table scroll");
  scrollbar.setAttribute("aria-orientation", "horizontal");
  scrollbar.setAttribute("role", "scrollbar");
  scrollbar.tabIndex = 0;
  scrollbarTrack.className = "floating-table-scrollbar-track";
  scrollbarThumb.className = "floating-table-scrollbar-thumb";
  scrollbarTrack.appendChild(scrollbarThumb);
  scrollbar.appendChild(scrollbarTrack);
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
        return isVisible(wrapper)
          && hasHorizontalOverflow
          && crossesViewport;
      });

    if (!candidates.length) return null;

    return candidates.reduce((best, wrapper) => {
      if (!best) return wrapper;
      const wrapperRect = wrapper.getBoundingClientRect();
      const bestRect = best.getBoundingClientRect();
      return Math.max(wrapperRect.top, 0) >= Math.max(bestRect.top, 0) ? wrapper : best;
    }, null);
  }

  function getScrollMetrics() {
    if (!activeWrapper) return null;

    const scrollRange = Math.max(activeWrapper.scrollWidth - activeWrapper.clientWidth, 0);
    const trackWidth = scrollbarTrack.clientWidth;
    const proportionalWidth = activeWrapper.scrollWidth
      ? trackWidth * (activeWrapper.clientWidth / activeWrapper.scrollWidth)
      : trackWidth;
    const thumbWidth = Math.min(trackWidth, Math.max(MIN_THUMB_WIDTH, proportionalWidth));

    return {
      scrollRange,
      thumbRange: Math.max(trackWidth - thumbWidth, 0),
      thumbWidth
    };
  }

  function syncFromWrapper() {
    if (!activeWrapper || syncing) return;

    const metrics = getScrollMetrics();
    if (!metrics) return;

    const thumbLeft = metrics.scrollRange
      ? (activeWrapper.scrollLeft / metrics.scrollRange) * metrics.thumbRange
      : 0;

    scrollbarThumb.style.width = `${metrics.thumbWidth}px`;
    scrollbarThumb.style.transform = `translateX(${thumbLeft}px)`;
    scrollbar.setAttribute("aria-valuemin", "0");
    scrollbar.setAttribute("aria-valuemax", `${Math.round(metrics.scrollRange)}`);
    scrollbar.setAttribute("aria-valuenow", `${Math.round(activeWrapper.scrollLeft)}`);
  }

  function setScrollLeft(value) {
    if (!activeWrapper) return;
    const metrics = getScrollMetrics();
    if (!metrics) return;

    syncing = true;
    activeWrapper.scrollLeft = Math.min(Math.max(value, 0), metrics.scrollRange);
    syncing = false;
    syncFromWrapper();
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
    scrollbar.classList.add("is-visible");
    syncFromWrapper();
  }

  function queueUpdate() {
    if (updateQueued) return;
    updateQueued = true;
    window.requestAnimationFrame(updateScrollbar);
  }

  scrollbar.addEventListener("pointerdown", event => {
    if (!activeWrapper || event.button !== 0) return;

    event.preventDefault();
    const metrics = getScrollMetrics();
    if (!metrics) return;

    if (event.target !== scrollbarThumb) {
      const trackRect = scrollbarTrack.getBoundingClientRect();
      const thumbLeft = Math.min(
        Math.max(event.clientX - trackRect.left - (metrics.thumbWidth / 2), 0),
        metrics.thumbRange
      );
      setScrollLeft(metrics.thumbRange
        ? (thumbLeft / metrics.thumbRange) * metrics.scrollRange
        : 0);
    }

    dragging = true;
    dragStartX = event.clientX;
    dragStartScrollLeft = activeWrapper.scrollLeft;
    scrollbar.classList.add("is-dragging");
    scrollbar.setPointerCapture(event.pointerId);
  });

  scrollbar.addEventListener("pointermove", event => {
    if (!dragging || !activeWrapper) return;

    const metrics = getScrollMetrics();
    if (!metrics || !metrics.thumbRange) return;
    const scrollDelta = (event.clientX - dragStartX)
      * (metrics.scrollRange / metrics.thumbRange);
    setScrollLeft(dragStartScrollLeft + scrollDelta);
  });

  function stopDragging(event) {
    if (!dragging) return;
    dragging = false;
    scrollbar.classList.remove("is-dragging");

    if (scrollbar.hasPointerCapture(event.pointerId)) {
      scrollbar.releasePointerCapture(event.pointerId);
    }
  }

  scrollbar.addEventListener("pointerup", stopDragging);
  scrollbar.addEventListener("pointercancel", stopDragging);

  scrollbar.addEventListener("wheel", event => {
    if (!activeWrapper) return;
    event.preventDefault();
    const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY)
      ? event.deltaX
      : event.deltaY;
    setScrollLeft(activeWrapper.scrollLeft + delta);
  }, { passive: false });

  scrollbar.addEventListener("keydown", event => {
    if (!activeWrapper) return;

    const pageStep = Math.max(activeWrapper.clientWidth * 0.8, 80);
    const keyActions = {
      ArrowLeft: () => setScrollLeft(activeWrapper.scrollLeft - 60),
      ArrowRight: () => setScrollLeft(activeWrapper.scrollLeft + 60),
      PageUp: () => setScrollLeft(activeWrapper.scrollLeft - pageStep),
      PageDown: () => setScrollLeft(activeWrapper.scrollLeft + pageStep),
      Home: () => setScrollLeft(0),
      End: () => setScrollLeft(activeWrapper.scrollWidth)
    };
    const action = keyActions[event.key];

    if (action) {
      event.preventDefault();
      action();
    }
  });

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
