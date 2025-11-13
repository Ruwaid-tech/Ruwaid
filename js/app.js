/*
  Reflective Cycling Journal interactions
  ---------------------------------------
  This file keeps JavaScript light and purposeful. Features include:
  - Loading reflection data across pages and computing the current-week entry count.
  - Rendering interactive route cards with filter persistence and accessible dialogs.
  - Allowing highlight-only views and scroll memory on the reflections page.
  Feel free to adjust arrays or copy the template objects for new content.
*/

const state = {
  reflections: [],
  entriesThisWeek: 0,
  highlightsOnly: false,
  routeFilter: 'all',
  reflectionsLoaded: false
};

const routesData = [
  {
    id: 'marina-loop',
    title: 'Marina Dawn Loop',
    distance: '12 km',
    terrain: 'easy',
    note: 'Gentle spins along the waterfront to start the day mindfully.',
    description: 'Begin at the east pier, loop around the marina, and follow the shared path past the sculpture garden before circling back.',
    safety: 'Watch for pedestrians near the cafes between 7&ndash;8am and use front lights if starting before sunrise.',
    highlights: ['Sunrise reflections on the harbour', 'Wide bike lanes with minimal traffic', 'Caf&eacute; stop for stretching halfway'],
    scenic: 'Sculpture Garden Boardwalk, Harbour Outlook Deck, Seabird Cove',
    dateTag: 'Ideal for calm mornings and recovery rides.',
    tags: ['easy', 'coastal', 'morning']
  },
  {
    id: 'ridgeway-crest',
    title: 'Ridgeway Crest Challenge',
    distance: '26 km',
    terrain: 'hilly',
    note: 'Rolling hills with two steep climbs&mdash;perfect for building endurance.',
    description: 'Navigate out of town via Ridgeway Road, climb the crest, and descend through forest switchbacks with wide shoulders.',
    safety: 'Carry extra hydration; winds increase on the crest. Descend cautiously on switchbacks.',
    highlights: ['Overlook bench ideal for breathing exercises', 'Birdsong-rich forest section', 'Quick access to roadside assistance pull-off'],
    scenic: 'Summit Vista Point, Pine Bend Overlook, Forest Switchbacks',
    dateTag: 'Best attempted on clear afternoons with low traffic.',
    tags: ['hilly', 'nature', 'afternoon']
  },
  {
    id: 'coastal-glide',
    title: 'Coastal Glide Path',
    distance: '18 km',
    terrain: 'coastal',
    note: 'Flat seaside ride with breezy sections and seagull company.',
    description: 'Start at the lighthouse, follow the shoreline trail, and loop through the wetlands bird sanctuary before returning via the promenade.',
    safety: 'Check tides for spray and wear reflective bands during fog.',
    highlights: ['Boardwalk planks resonate with cadence', 'Pelican lookout tower pause', 'Quiet fishing village smells inspiring reflection'],
    scenic: 'Beacon Lighthouse, Sand Dune Preserve, Wetlands Sanctuary',
    dateTag: 'Pair with weekend afternoons when the tide is low.',
    tags: ['coastal', 'easy', 'weekend']
  },
  {
    id: 'river-park',
    title: 'River Park Connector',
    distance: '22 km',
    terrain: 'moderate',
    note: 'Winding path with light gravel sections and shady stretches.',
    description: 'Link the north and south parks via the riverside connector, taking the pedestrian bridge and looping the arboretum trail.',
    safety: 'Gravel corners can be loose after rain&mdash;slow before turns and ring bell over bridges.',
    highlights: ['Arboretum canopy tunnel', 'Picnic lawn reflection break', 'Bridge views of kayakers'],
    scenic: 'North Park Meadow, Riverside Bridge, Arboretum Loop',
    dateTag: 'Comfortable in late mornings with diffused light.',
    tags: ['moderate', 'nature', 'bridge']
  },
  {
    id: 'urban-mural-tour',
    title: 'Urban Mural Tour',
    distance: '15 km',
    terrain: 'easy',
    note: 'City ride connecting street art, pocket parks, and cozy cafes.',
    description: 'Trace the mural map from the arts district, weave through safe bike lanes, and pause at community gardens.',
    safety: 'Use bright lights in tunnels and obey downtown bike signals.',
    highlights: ['Interactive mural selfie spots', 'Community garden volunteers to interview', 'Pop-up caf&eacute; with friendly baristas'],
    scenic: 'Arts District Plaza, Garden Walk, Riverside Alley Gallery',
    dateTag: 'Great for weekend culture rides with friends.',
    tags: ['easy', 'urban', 'afternoon']
  },
  {
    id: 'lake-horizon',
    title: 'Lake Horizon Circuit',
    distance: '30 km',
    terrain: 'moderate',
    note: 'Longer loop circling the lake with gentle rollers and wildlife spotting.',
    description: 'Ride clockwise from the boathouse, share the multi-use path, and stop at the environmental center deck for journaling.',
    safety: 'Carry spare tube; lakeside path may have driftwood after storms.',
    highlights: ['Quiet bays for deep breathing', 'Observation deck journaling break', 'Wide shoulders through farm roads'],
    scenic: 'Boathouse Start, Environmental Center, South Shore Farms',
    dateTag: 'Plan for golden-hour finishes to catch sunset colors.',
    tags: ['moderate', 'sunset', 'nature']
  }
];

const page = document.body?.dataset.page ?? 'home';
const reflectionsUrl = 'data/reflections.json';
let reflectionsPromise;

const getReflections = () => {
  if (!reflectionsPromise) {
    reflectionsPromise = fetch(reflectionsUrl)
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load reflections data.');
        return response.json();
      })
      .then((data) => {
        state.reflections = Array.isArray(data) ? data : [];
        state.reflectionsLoaded = true;
        computeEntriesThisWeek();
        updateTestState();
        return state.reflections;
      })
      .catch((error) => {
        console.error(error);
        state.reflections = [];
        state.reflectionsLoaded = false;
        updateTestState();
        throw error;
      });
  }
  return reflectionsPromise;
};

const computeEntriesThisWeek = () => {
  if (!state.reflections.length) {
    state.entriesThisWeek = 0;
    return;
  }
  const now = new Date();
  const startOfWeek = new Date(now);
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  startOfWeek.setDate(diff);
  startOfWeek.setHours(0, 0, 0, 0);

  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 7);

  state.entriesThisWeek = state.reflections.filter((entry) => {
    const entryDate = new Date(entry.date);
    return entryDate >= startOfWeek && entryDate < endOfWeek;
  }).length;
};

const updateHomeStats = () => {
  const statEl = document.querySelector('[data-testid="entries-this-week"]');
  if (!statEl) return;
  statEl.textContent = state.entriesThisWeek.toString();
};

const renderReflections = (entries) => {
  const loader = document.getElementById('reflections-loader');
  const container = document.getElementById('reflections-container');
  if (!loader || !container) return;

  container.innerHTML = '';
  const template = document.getElementById('reflection-card-template');

  entries.forEach((entry) => {
    const clone = template.content.cloneNode(true);
    const card = clone.querySelector('.reflection-card');
    card.dataset.entryId = entry.id;
    card.dataset.hasInsight = entry.insight ? 'true' : 'false';

    clone.querySelector('.reflection-date').textContent = new Intl.DateTimeFormat('en', {
      dateStyle: 'long'
    }).format(new Date(entry.date));
    clone.querySelector('.reflection-summary').textContent = entry.summary;
    clone.querySelector('.reflection-mood').textContent = `Mood: ${entry.mood}`;
    const insightEl = clone.querySelector('.reflection-insight');
    if (entry.insight) {
      insightEl.textContent = entry.insight;
      insightEl.setAttribute('aria-label', 'Highlighted insight');
    } else {
      insightEl.textContent = 'No specific highlight noted for this ride.';
      insightEl.classList.add('muted');
      card.dataset.hasInsight = 'false';
    }

    const photoFigure = clone.querySelector('.reflection-photo');
    if (entry.photo) {
      const img = photoFigure.querySelector('img');
      img.src = entry.photo;
      img.alt = entry.summary;
      photoFigure.querySelector('figcaption').textContent = 'Route photo: ' + entry.routeId.replace(/-/g, ' ');
      photoFigure.hidden = false;
    }

    const tagsWrapper = clone.querySelector('.reflection-tags');
    (entry.tags || []).forEach((tag) => {
      const span = document.createElement('span');
      span.className = 'chip';
      span.textContent = tag;
      tagsWrapper.appendChild(span);
    });

    container.appendChild(clone);
  });

  loader.hidden = true;
  container.hidden = false;
};

const filterReflectionsByHighlights = () => {
  const container = document.getElementById('reflections-container');
  if (!container) return;

  container.querySelectorAll('.reflection-card').forEach((card) => {
    const hasInsight = card.dataset.hasInsight === 'true';
    card.hidden = state.highlightsOnly && !hasInsight;
  });
};

const handleHighlightToggle = (button) => {
  state.highlightsOnly = !state.highlightsOnly;
  button.setAttribute('aria-pressed', String(state.highlightsOnly));
  button.textContent = state.highlightsOnly ? 'Show all entries' : 'Show highlights only';
  filterReflectionsByHighlights();
  announce(`Highlight filter ${state.highlightsOnly ? 'enabled' : 'cleared'}.`);
  updateTestState();
};

const renderRoutes = (routes) => {
  const container = document.getElementById('routes-container');
  const template = document.getElementById('route-card-template');
  if (!container || !template) return;

  container.innerHTML = '';

  routes.forEach((route) => {
    const clone = template.content.cloneNode(true);
    const card = clone.querySelector('.route-card');
    card.dataset.routeId = route.id;
    card.dataset.tags = route.tags.join(',');

    clone.querySelector('.route-title').textContent = route.title;
    clone.querySelector('.route-meta').textContent = `${route.distance} · ${route.terrain}`;
    clone.querySelector('.route-note').innerHTML = route.note;

    const tagWrapper = clone.querySelector('.route-tags');
    route.tags.forEach((tag) => {
      const span = document.createElement('span');
      span.className = 'chip';
      span.textContent = tag;
      tagWrapper.appendChild(span);
    });

    const button = clone.querySelector('[data-action="open-details"]');
    button.addEventListener('click', () => openRouteDialog(route));

    container.appendChild(clone);
  });
};

let activeDialog = null;
let lastFocusedElement = null;

const openRouteDialog = (route) => {
  closeRouteDialog();
  const template = document.getElementById('route-dialog-template');
  if (!template) return;

  const clone = template.content.cloneNode(true);
  const dialog = clone.querySelector('.route-dialog');
  dialog.dataset.routeId = route.id;
  const content = clone.querySelector('.dialog-content');

  clone.querySelector('#route-dialog-title').textContent = route.title;
  clone.querySelector('.dialog-meta').textContent = `${route.distance} · ${route.terrain}`;
  clone.querySelector('.dialog-description').innerHTML = `<strong>Route overview:</strong> ${route.description}`;
  clone.querySelector('.dialog-safety').innerHTML = `<strong>Safety notes:</strong> ${route.safety}`;
  const highlights = clone.querySelector('.dialog-highlights');
  route.highlights.forEach((item) => {
    const li = document.createElement('li');
    li.innerHTML = item;
    highlights.appendChild(li);
  });
  clone.querySelector('.dialog-date').innerHTML = `<strong>Planning notes:</strong> ${route.dateTag}`;

  const closeBtn = clone.querySelector('[data-action="close-dialog"]');
  closeBtn.addEventListener('click', () => closeRouteDialog());

  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) {
      closeRouteDialog();
    }
  });

  const handleKeydown = (event) => {
    if (event.key === 'Escape') {
      closeRouteDialog();
    }
    if (event.key === 'Tab') {
      trapFocus(event, content);
    }
  };

  dialog.addEventListener('keydown', handleKeydown);
  document.body.appendChild(dialog);
  activeDialog = dialog;
  lastFocusedElement = document.activeElement;
  closeBtn.focus();
};

const trapFocus = (event, container) => {
  const focusable = container.querySelectorAll('a, button, textarea, input, select, [tabindex]:not([tabindex="-1"])');
  const focusableElements = Array.from(focusable).filter((el) => !el.hasAttribute('disabled'));
  if (!focusableElements.length) return;

  const first = focusableElements[0];
  const last = focusableElements[focusableElements.length - 1];

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
};

const closeRouteDialog = () => {
  if (!activeDialog) return;
  activeDialog.remove();
  activeDialog = null;
  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
};

const filterRoutes = (filterValue) => {
  const filtered = routesData.filter((route) => {
    if (filterValue === 'all') return true;
    return route.tags.includes(filterValue);
  });
  renderRoutes(filtered);
  const feedback = document.getElementById('filter-feedback');
  if (feedback) {
    const suffix = filterValue === 'all' ? '' : ` tagged “${filterValue}”`;
    feedback.textContent = `Showing ${filtered.length} routes${suffix}.`;
  }
  announce('Routes updated.');
  updateTestState();
};

const announce = (message) => {
  let region = document.getElementById('live-region');
  if (!region) {
    region = document.createElement('div');
    region.id = 'live-region';
    region.className = 'visually-hidden';
    region.setAttribute('role', 'status');
    region.setAttribute('aria-live', 'polite');
    document.body.appendChild(region);
  }
  region.textContent = message;
};

const initRoutesPage = () => {
  const select = document.querySelector('[data-testid="route-filter"]');
  const saved = localStorage.getItem('route-filter-value');
  if (saved) {
    state.routeFilter = saved;
    if (select) select.value = saved;
  }
  filterRoutes(state.routeFilter);
  if (select) {
    select.addEventListener('change', (event) => {
      const value = event.target.value;
      state.routeFilter = value;
      localStorage.setItem('route-filter-value', value);
      filterRoutes(value);
    });
  }
};

const initReflectionsPage = async () => {
  const toggleButton = document.querySelector('[data-action="toggle-highlights"]');
  if (toggleButton) {
    toggleButton.addEventListener('click', () => handleHighlightToggle(toggleButton));
  }

  try {
    const reflections = await getReflections();
    renderReflections(reflections);
    filterReflectionsByHighlights();
  } catch (error) {
    const loader = document.getElementById('reflections-loader');
    if (loader) {
      loader.textContent = 'Reflections could not be loaded. Please check data/reflections.json.';
    }
  }

  restoreScrollPosition();
  setupScrollMemory();
};

const initHomePage = async () => {
  try {
    await getReflections();
  } catch (error) {
    console.error(error);
  }
  updateHomeStats();
};

const setupBackToTop = () => {
  const button = document.querySelector('.back-to-top');
  if (!button) return;

  const toggleVisibility = () => {
    if (window.scrollY > 320) {
      button.classList.add('is-visible');
    } else {
      button.classList.remove('is-visible');
    }
  };

  toggleVisibility();
  window.addEventListener('scroll', toggleVisibility, { passive: true });
  button.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
};

const setupYear = () => {
  const yearEl = document.getElementById('year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
};

const setupScrollMemory = () => {
  if (page !== 'reflections') return;
  let timer;
  window.addEventListener('scroll', () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      sessionStorage.setItem('reflections-scroll', String(window.scrollY));
    }, 200);
  }, { passive: true });
};

const restoreScrollPosition = () => {
  if (page !== 'reflections') return;
  const stored = sessionStorage.getItem('reflections-scroll');
  if (stored) {
    requestAnimationFrame(() => {
      window.scrollTo(0, Number(stored));
    });
  }
};

const updateTestState = () => {
  window.TEST = () => ({
    entriesThisWeek: state.entriesThisWeek,
    routeFilter: state.routeFilter,
    highlightsOnly: state.highlightsOnly,
    reflectionsLoaded: state.reflectionsLoaded,
    reflectionsCount: state.reflections.length
  });
};

const init = () => {
  setupYear();
  setupBackToTop();
  updateTestState();

  if (page === 'home') {
    initHomePage();
  }

  if (page === 'routes') {
    initRoutesPage();
  }

  if (page === 'reflections') {
    initReflectionsPage();
  }
};

init();
