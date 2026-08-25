import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { API_URL, ApiError, authStorage, endpoints, resolveMediaUrl } from "./api";
import "./styles.css";

const Icons = {
  logo: (props = {}) => <svg viewBox="0 0 40 40" {...props}><path d="M20 4c7.8 0 14 6.2 14 14 0 9.3-10.5 17.2-14 18-3.5-.8-14-8.7-14-18C6 10.2 12.2 4 20 4Z" fill="currentColor" opacity=".16"/><path d="M20 10a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm0 4.2a3.8 3.8 0 1 1 0 7.6 3.8 3.8 0 0 1 0-7.6Z" fill="currentColor"/></svg>,
  search: () => <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>,
  user: () => <svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>,
  calendar: () => <svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>,
  clock: () => <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>,
  pin: () => <svg viewBox="0 0 24 24"><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>,
  star: () => <svg viewBox="0 0 24 24"><path d="m12 3 2.7 5.5 6 .9-4.4 4.2 1 6-5.3-2.8-5.3 2.8 1-6-4.4-4.2 6-.9L12 3Z"/></svg>,
  chevron: () => <svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></svg>,
  arrow: () => <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>,
  menu: () => <svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg>,
  close: () => <svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>,
  logout: () => <svg viewBox="0 0 24 24"><path d="M10 5H5v14h5M14 16l4-4-4-4M18 12H9"/></svg>,
  image: () => <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 20"/></svg>,
  trash: () => <svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13M10 11v5M14 11v5"/></svg>,
  edit: () => <svg viewBox="0 0 24 24"><path d="m4 20 4.3-1 10.9-10.9-3.3-3.3L5 15.7 4 20ZM14.7 6l3.3 3.3"/></svg>,
  plus: () => <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>,
  grid: () => <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>,
  briefcase: () => <svg viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V4h6v3M3 12h18"/></svg>,
  settings: () => <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.4 1A7 7 0 0 0 15 6l-.3-2.6h-4L10.5 6A7 7 0 0 0 9 7.1l-2.4-1-2 3.4 2 1.5a7 7 0 0 0 0 2l-2 1.5 2 3.4 2.4-1a7 7 0 0 0 1.5 1.1l.3 2.6h4L15 18a7 7 0 0 0 1.5-1.1l2.4 1 2-3.4-2-1.5c.1-.3.1-.7.1-1Z"/></svg>,
};

function Icon({ name, size = 20, className = "" }) {
  const Component = Icons[name];
  return <span className={`icon ${className}`} style={{ width: size, height: size }}>{Component ? <Component /> : null}</span>;
}

const AuthContext = createContext(null);
const ToastContext = createContext(() => {});

function useAuth() { return useContext(AuthContext); }
function useToast() { return useContext(ToastContext); }

function useHashRoute() {
  const getRoute = () => window.location.hash.replace(/^#/, "") || "/";
  const [route, setRoute] = useState(getRoute);
  useEffect(() => {
    const listener = () => setRoute(getRoute());
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  return route;
}

function go(path) {
  if (window.location.hash.replace(/^#/, "") === path) {
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  } else {
    window.location.hash = path;
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function safeError(error, fallback = "Не удалось выполнить действие") {
  return error instanceof ApiError ? error.message : error?.message || fallback;
}

function formatMoney(value) {
  const number = Number(value || 0);
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(number) + " ₽";
}

function formatDate(dateValue) {
  if (!dateValue) return "—";
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", year: "numeric" }).format(new Date(dateValue));
}

function todayIso() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function rootCategories(categories) {
  return categories.filter((category) => !category.parent_id);
}

function categoryChildren(categories, parentId) {
  return categories.filter((category) => category.parent_id === parentId);
}

function categoryPath(categories, categoryId) {
  if (!categoryId) return [];
  const byId = new Map(categories.map((category) => [category.id, category]));
  const path = [];
  const seen = new Set();
  let current = byId.get(categoryId);

  while (current && !seen.has(current.id)) {
    path.unshift(current.id);
    seen.add(current.id);
    current = current.parent_id ? byId.get(current.parent_id) : null;
  }

  return path;
}

function CategoryCascade({ categories, value, onChange, requireLeaf = false, allowAll = false }) {
  const [path, setPath] = useState([]);

  useEffect(() => {
    if (!categories.length) return;

    if (value) {
      const nextPath = categoryPath(categories, value);
      if (nextPath.join("/") !== path.join("/")) setPath(nextPath);
      return;
    }

    if (!requireLeaf && path.length) setPath([]);
  }, [categories, value, requireLeaf, path]);

  const roots = rootCategories(categories);
  const levels = [roots];
  let parentId = path[0];

  for (let level = 1; parentId; level += 1) {
    const children = categoryChildren(categories, parentId);
    if (!children.length) break;
    levels.push(children);
    parentId = path[level];
  }

  const selectAtLevel = (level, categoryId) => {
    if (!categoryId) {
      const nextPath = path.slice(0, level);
      setPath(nextPath);
      const parent = nextPath.at(-1);
      onChange(requireLeaf ? "" : parent || "");
      return;
    }

    const nextPath = [...path.slice(0, level), categoryId];
    setPath(nextPath);
    const hasChildren = categoryChildren(categories, categoryId).length > 0;
    onChange(requireLeaf && hasChildren ? "" : categoryId);
  };

  return (
    <div className="category-cascade">
      {levels.map((options, level) => {
        const selected = path[level] || "";
        const label = level === 0 ? "Основная категория" : level === 1 ? "Подкатегория" : `Уровень ${level + 1}`;
        const placeholder = level === 0
          ? (allowAll ? "Все категории" : "Выберите категорию")
          : (requireLeaf ? "Выберите подкатегорию" : "Все подкатегории");

        return (
          <div className="category-cascade-level" key={level}>
            <div className="category-cascade-label">
              <span>{level + 1}</span>
              <b>{label}</b>
            </div>
            <select
              required={requireLeaf}
              value={selected}
              onChange={(event) => selectAtLevel(level, event.target.value)}
            >
              <option value="">{placeholder}</option>
              {options.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
            </select>
          </div>
        );
      })}
      {requireLeaf && path.length > 0 && categoryChildren(categories, path.at(-1)).length > 0 && (
        <div className="category-cascade-note">Выберите точную подкатегорию, к которой относится услуга.</div>
      )}
    </div>
  );
}

const weekDays = [
  ["monday", "Понедельник"], ["tuesday", "Вторник"], ["wednesday", "Среда"],
  ["thursday", "Четверг"], ["friday", "Пятница"], ["saturday", "Суббота"], ["sunday", "Воскресенье"],
];

const statusLabels = {
  pending: "Ожидает подтверждения",
  confirmed: "Подтверждено",
  completed: "Завершено",
  cancelled: "Отменено",
};

function App() {
  const route = useHashRoute();
  const [user, setUser] = useState(null);
  const [avatarUrl, setAvatarUrl] = useState(null);
  const [authLoading, setAuthLoading] = useState(Boolean(authStorage.get()));
  const [toast, setToast] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const notify = useCallback((message, type = "success") => {
    setToast({ message, type, id: Date.now() });
  }, []);

  const refreshUser = useCallback(async () => {
    if (!authStorage.get()) {
      setUser(null);
      setAvatarUrl(null);
      setAuthLoading(false);
      return null;
    }
    try {
      const current = await endpoints.me();
      setUser(current);
      const storedAvatar = localStorage.getItem(`masterbooking_avatar_url:${current.id}`);
      setAvatarUrl(current.avatar_url ? resolveMediaUrl(current.avatar_url) : storedAvatar || null);
      return current;
    } catch {
      setUser(null);
      setAvatarUrl(null);
      authStorage.clear();
      return null;
    } finally {
      setAuthLoading(false);
    }
  }, []);

  useEffect(() => { refreshUser(); }, [refreshUser]);
  useEffect(() => { setMobileOpen(false); }, [route]);
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 3600);
    return () => clearTimeout(id);
  }, [toast]);

  const authValue = useMemo(() => ({
    user,
    avatarUrl,
    authLoading,
    refreshUser,
    setUploadedAvatar(url) {
      if (!user?.id || !url) return;
      const resolved = resolveMediaUrl(url);
      const versioned = `${resolved}${resolved.includes("?") ? "&" : "?"}v=${Date.now()}`;
      localStorage.setItem(`masterbooking_avatar_url:${user.id}`, versioned);
      setAvatarUrl(versioned);
    },
    clearUploadedAvatar() {
      if (user?.id) localStorage.removeItem(`masterbooking_avatar_url:${user.id}`);
      setAvatarUrl(null);
    },
    async login(email, password) {
      const response = await endpoints.login(email, password);
      authStorage.set(response.access_token);
      await refreshUser();
      return response;
    },
    async register(data) {
      await endpoints.register(data);
      const response = await endpoints.login(data.email, data.password);
      authStorage.set(response.access_token);
      await refreshUser();
    },
    logout() {
      authStorage.clear();
      setUser(null);
      setAvatarUrl(null);
      go("/");
    },
  }), [user, avatarUrl, authLoading, refreshUser]);

  let page;
  if (route === "/" || route === "") page = <HomePage />;
  else if (route.startsWith("/catalog")) page = <CatalogPage route={route} />;
  else if (route.startsWith("/offering/")) page = <OfferingPage id={route.split("/")[2]} />;
  else if (route === "/auth") page = <AuthPage />;
  else if (route === "/profile") page = <Protected><ProfilePage /></Protected>;
  else if (route === "/become-master") page = <Protected><BecomeMasterPage /></Protected>;
  else if (route.startsWith("/master")) page = <Protected role="master"><MasterDashboard route={route} /></Protected>;
  else if (route === "/admin") page = <Protected role="admin"><AdminPage /></Protected>;
  else page = <NotFound />;

  return (
    <ToastContext.Provider value={notify}>
      <AuthContext.Provider value={authValue}>
        <div className="app-shell">
          <Header mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />
          <main>{page}</main>
          <Footer />
          {toast && <Toast toast={toast} onClose={() => setToast(null)} />}
        </div>
      </AuthContext.Provider>
    </ToastContext.Provider>
  );
}

function Protected({ children, role }) {
  const { user, authLoading } = useAuth();
  if (authLoading) return <PageLoader />;
  if (!user) return <AuthRequired />;
  if (role && user.role !== role) return <AccessDenied />;
  return children;
}

function Header({ mobileOpen, setMobileOpen }) {
  const { user, avatarUrl, logout } = useAuth();
  return (
    <header className="site-header">
      <div className="container header-inner">
        <button className="brand" onClick={() => go("/")} aria-label="MasterBooking">
          <span className="brand-mark"><Icon name="logo" size={34} /></span>
          <span>MasterBooking</span>
        </button>
        <nav className={`main-nav ${mobileOpen ? "is-open" : ""}`}>
          <button onClick={() => go("/catalog")}>Каталог услуг</button>
          <button onClick={() => go("/catalog?sort=popular")}>Популярные услуги</button>
          {user?.role === "master" && <button onClick={() => go("/master")}>Кабинет мастера</button>}
          {user?.role === "admin" && <button onClick={() => go("/admin")}>Администрирование</button>}
        </nav>
        <div className="header-actions">
          {user ? (
            <>
              <button className="profile-pill" onClick={() => go(user.role === "master" ? "/master" : user.role === "admin" ? "/admin" : "/profile")}>
                <span className="avatar avatar-sm">{avatarUrl ? <img src={avatarUrl} alt="Аватар"/> : <>{user.first_name?.[0]}{user.last_name?.[0]}</>}</span>
                <span className="profile-pill-copy"><b>{user.first_name}</b><small>{user.role === "master" ? "Мастер" : user.role === "admin" ? "Администратор" : "Клиент"}</small></span>
              </button>
              <button className="icon-button desktop-only" title="Выйти" onClick={logout}><Icon name="logout" /></button>
            </>
          ) : (
            <button className="button button-dark button-small desktop-only" onClick={() => go("/auth")}>Войти</button>
          )}
          <button className="icon-button mobile-menu-button" onClick={() => setMobileOpen(!mobileOpen)}><Icon name={mobileOpen ? "close" : "menu"} /></button>
        </div>
      </div>
      {mobileOpen && (
        <div className="mobile-panel">
          {!user ? <button className="button button-dark" onClick={() => go("/auth")}>Войти или зарегистрироваться</button> : <button className="button button-ghost" onClick={logout}>Выйти</button>}
        </div>
      )}
    </header>
  );
}

function Footer() {
  const { user } = useAuth();
  const masterPath = user?.role === "master" ? "/master" : "/become-master";
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div><div className="brand brand-footer"><span className="brand-mark"><Icon name="logo" size={30} /></span><span>MasterBooking</span></div><p>Платформа для поиска услуг и онлайн-записи к мастерам по актуальному расписанию.</p></div>
        <div><b>Клиентам</b><button onClick={() => go("/catalog")}>Каталог услуг</button><button onClick={() => go("/profile")}>Мои записи</button></div>
        <div><b>Мастерам</b><button onClick={() => go(masterPath)}>{user?.role === "master" ? "Кабинет мастера" : "Подключиться как мастер"}</button>{user?.role === "master" && <button onClick={() => go("/master")}>Расписание и записи</button>}</div>
        <div><b>API</b><span>{API_URL}</span><span>FastAPI + React</span></div>
      </div>
      <div className="container footer-bottom">© {new Date().getFullYear()} MasterBooking. Сервис онлайн-записи.</div>
    </footer>
  );
}

function HomePage() {
  const { user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [offerings, setOfferings] = useState([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let mounted = true;

    endpoints.categories()
      .then((items) => { if (mounted) setCategories(rootCategories(items).slice(0, 8)); })
      .catch(() => { if (mounted) setCategories([]); })
      .finally(() => { if (mounted) setCategoriesLoading(false); });

    endpoints.offerings({ page_size: 6, sort: "popular" })
      .then((data) => { if (mounted) setOfferings(data.items || []); })
      .catch(() => { if (mounted) setOfferings([]); });

    return () => { mounted = false; };
  }, []);

  const submit = (event) => {
    event.preventDefault();
    go(`/catalog?search=${encodeURIComponent(query.trim())}`);
  };

  const openMasterArea = () => go(user?.role === "master" ? "/master" : "/become-master");
  const quickCategories = categories.slice(0, 4);
  const previewOfferings = offerings.slice(0, 3);

  return (
    <>
      <section className="hero-section hero-section-pro">
        <div className="container hero-grid hero-grid-pro">
          <div className="hero-copy hero-copy-pro">
            <div className="eyebrow">Онлайн-запись к мастерам</div>
            <h1>Найдите услугу.<br/><em>Выберите время.</em><br/>Запишитесь онлайн.</h1>
            <p>Сравнивайте услуги по цене, рейтингу и расположению. Выбирайте свободное время в актуальном расписании мастера — без звонков и ожидания ответа.</p>

            <form className="hero-search hero-search-pro" onSubmit={submit}>
              <Icon name="search" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Услуга, например массаж или стрижка"
                aria-label="Поиск услуг"
              />
              <button className="button button-accent">Найти услугу</button>
            </form>

            {quickCategories.length > 0 && (
              <div className="hero-quick-links">
                <span>Популярные направления</span>
                <div>
                  {quickCategories.map((category) => (
                    <button key={category.id} onClick={() => go(`/catalog?category_id=${category.id}`)}>{category.name}</button>
                  ))}
                </div>
              </div>
            )}

            <div className="hero-trust-row">
              <div><span className="hero-trust-icon">✓</span><p><b>Актуальное расписание</b><small>Свободные слоты рассчитываются автоматически</small></p></div>
              <div><span className="hero-trust-icon">★</span><p><b>Отзывы после визита</b><small>Оценку оставляют реальные клиенты</small></p></div>
            </div>
          </div>

          <div className="hero-discovery" aria-label="Пример доступных услуг">
            <div className="hero-discovery-head">
              <div>
                <span className="eyebrow hero-panel-eyebrow">Доступно для записи</span>
                <h2>Выберите подходящий вариант</h2>
              </div>
              <span className="hero-live-badge"><i></i> Онлайн</span>
            </div>

            <div className="hero-location-pill"><Icon name="pin" size={16}/><span>Поиск по вашему городу и району</span></div>

            <div className="hero-service-stack">
              {previewOfferings.length ? previewOfferings.map((item, index) => (
                <button className="hero-service-preview" key={item.id} onClick={() => go(`/offering/${item.id}`)}>
                  <span className={`hero-service-avatar hero-service-avatar-${(index % 3) + 1}`}>
                    {item.master?.avatar_url ? (
                      <img
                        src={resolveMediaUrl(item.master.avatar_url)}
                        alt={`${item.master?.first_name || ""} ${item.master?.last_name || ""}`.trim() || "Аватар мастера"}
                      />
                    ) : (
                      <>{item.master?.first_name?.[0]}{item.master?.last_name?.[0]}</>
                    )}
                  </span>
                  <span className="hero-service-copy">
                    <b>{item.title}</b>
                    <small>{item.duration_minutes} мин · свободное время онлайн</small>
                  </span>
                  <span className="hero-service-price">{formatMoney(item.final_price ?? item.price)}</span>
                  <Icon name="chevron" size={17}/>
                </button>
              )) : (
                <>
                  <div className="hero-service-preview is-placeholder"><span className="hero-service-avatar hero-service-avatar-1">С</span><span className="hero-service-copy"><b>Стрижка и укладка</b><small>60 мин · запись онлайн</small></span><span className="hero-service-price">от 1 500 ₽</span></div>
                  <div className="hero-service-preview is-placeholder"><span className="hero-service-avatar hero-service-avatar-2">М</span><span className="hero-service-copy"><b>Классический массаж</b><small>60 мин · запись онлайн</small></span><span className="hero-service-price">от 2 000 ₽</span></div>
                  <div className="hero-service-preview is-placeholder"><span className="hero-service-avatar hero-service-avatar-3">Б</span><span className="hero-service-copy"><b>Оформление бровей</b><small>45 мин · запись онлайн</small></span><span className="hero-service-price">от 1 200 ₽</span></div>
                </>
              )}
            </div>

            <div className="hero-discovery-footer">
              <div><Icon name="calendar" size={19}/><span><b>Свободное время без переписки</b><small>После выбора услуги вы увидите доступные слоты мастера.</small></span></div>
              <button className="text-link" onClick={() => go("/catalog")}>Перейти в каталог <Icon name="arrow" size={16}/></button>
            </div>
          </div>
        </div>
      </section>

      <section className="section section-tight">
        <div className="container">
          <SectionHeader eyebrow="Направления" title="Выберите категорию услуг" action="Смотреть весь каталог" onAction={() => go("/catalog")} />
          <div className="category-grid">
            {categoriesLoading ? (
              Array.from({ length: 4 }).map((_, index) => (
                <div className="category-card category-skeleton" key={index}>
                  <span className="skeleton category-skeleton-art"></span>
                  <span className="category-skeleton-copy"><i className="skeleton"></i><i className="skeleton"></i></span>
                </div>
              ))
            ) : categories.length ? (
              categories.map((category, index) => (
                <button key={category.id} className="category-card" onClick={() => go(`/catalog?category_id=${category.id}`)}>
                  <span className={`category-art art-${(index % 6) + 1}`}>{category.name?.slice(0, 1) || "✦"}</span>
                  <span><b>{category.name}</b><small>Открыть услуги</small></span><Icon name="chevron" size={18}/>
                </button>
              ))
            ) : (
              <div className="category-empty">
                <div className="empty-icon"><Icon name="grid" size={28}/></div>
                <div><b>Каталог категорий пока пуст</b><span>Категории появятся здесь после публикации администратором.</span></div>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="section soft-section">
        <div className="container">
          <SectionHeader eyebrow="Популярное" title="Услуги, которые выбирают чаще" action="Открыть каталог" onAction={() => go("/catalog?sort=popular")} />
          <div className="offering-grid">
            {offerings.length ? offerings.map((item) => <OfferingCard key={item.id} item={item} />) : <DemoOfferingSkeletons />}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container steps-wrap">
          <SectionHeader eyebrow="Как это работает" title="От поиска до записи — три шага" />
          <div className="steps-grid">
            <Step number="01" title="Найдите подходящую услугу" text="Используйте категории, поиск и фильтры по локации, чтобы сравнить подходящие предложения." />
            <Step number="02" title="Выберите свободное время" text="Доступные слоты формируются из рабочего расписания мастера и уже созданных записей." />
            <Step number="03" title="Управляйте записью в кабинете" text="Следите за статусом записи, просматривайте детали и отменяйте визит при необходимости." />
          </div>
        </div>
      </section>

      <section className="section cta-section">
        <div className="container">
          <div className="cta-panel">
            <div><span className="eyebrow light">Для мастеров</span><h2>Организуйте запись клиентов в одном сервисе</h2><p>Публикуйте услуги, настраивайте рабочее время и управляйте входящими записями из личного кабинета.</p></div>
            <button className="button button-light" onClick={openMasterArea}>{user?.role === "master" ? "Перейти в кабинет" : "Создать профиль мастера"} <Icon name="arrow" /></button>
          </div>
        </div>
      </section>
    </>
  );
}

function SectionHeader({ eyebrow, title, action, onAction }) {
  return <div className="section-header"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2></div>{action && <button className="text-link" onClick={onAction}>{action}<Icon name="arrow" size={17}/></button>}</div>;
}

function Step({ number, title, text }) { return <div className="step-card"><span>{number}</span><h3>{title}</h3><p>{text}</p></div>; }

function DemoOfferingSkeletons() { return Array.from({ length: 3 }).map((_, i) => <div className="offering-card skeleton-card" key={i}><div className="skeleton skeleton-image"></div><div className="card-body"><div className="skeleton line wide"></div><div className="skeleton line"></div><div className="skeleton line short"></div></div></div>); }

function OfferingImage({ offeringId, alt, className = "" }) {
  const [image, setImage] = useState(null);
  useEffect(() => {
    let mounted = true;
    endpoints.offeringImages(offeringId).then((images) => {
      if (!mounted) return;
      const primary = images.find((item) => item.is_primary) || images[0];
      setImage(primary?.image_url ? resolveMediaUrl(primary.image_url) : null);
    }).catch(() => {});
    return () => { mounted = false; };
  }, [offeringId]);
  return image ? <img className={className} src={image} alt={alt} /> : <div className={`image-fallback ${className}`}><Icon name="image" size={34}/><span>{alt?.slice(0, 1) || "M"}</span></div>;
}

const masterRatingCache = new Map();

function loadMasterRating(masterId) {
  if (!masterId) return Promise.resolve({ average_rating: 0, reviews_count: 0 });
  if (!masterRatingCache.has(masterId)) {
    masterRatingCache.set(
      masterId,
      endpoints.masterReviewStats(masterId).catch(() => ({ average_rating: 0, reviews_count: 0 })),
    );
  }
  return masterRatingCache.get(masterId);
}

function MasterRating({ masterId }) {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    let mounted = true;
    loadMasterRating(masterId).then((data) => { if (mounted) setStats(data); });
    return () => { mounted = false; };
  }, [masterId]);

  if (!stats) return <span className="card-rating loading-rating"><Icon name="star" size={14}/>…</span>;
  if (!stats.reviews_count) return <span className="card-rating empty-rating"><Icon name="star" size={14}/>Нет оценок</span>;
  return <span className="card-rating"><Icon name="star" size={14}/><b>{Number(stats.average_rating || 0).toFixed(1)}</b><small>({stats.reviews_count})</small></span>;
}

function OfferingCard({ item, isOwn = false }) {
  const location = [item.master?.city, item.master?.district, item.master?.address].filter(Boolean).join(", ");
  const discountPercent = Number(item.discount_percent || 0);
  const hasDiscount = discountPercent > 0;
  const finalPrice = item.final_price ?? item.price;
  return (
    <article className="offering-card" onClick={() => go(`/offering/${item.id}`)}>
      <div className="offering-image-wrap"><OfferingImage offeringId={item.id} alt={item.title} className="offering-image"/><span className="duration-badge"><Icon name="clock" size={15}/>{item.duration_minutes} мин</span>{isOwn && <span className="own-offering-badge">Ваша услуга</span>}</div>
      <div className="card-body">
        <div className="tag-row">{item.tags?.slice(0, 2).map((tag) => <span className="tag" key={tag.id}>{tag.name}</span>)}</div>
        <h3>{item.title}</h3>
        <div className="master-summary">
          <div className="master-line">
            <span className="avatar avatar-xs">
              {item.master?.avatar_url ? (
                <img
                  src={resolveMediaUrl(item.master.avatar_url)}
                  alt={`${item.master?.first_name || ""} ${item.master?.last_name || ""}`.trim() || "Аватар мастера"}
                />
              ) : (
                <>{item.master?.first_name?.[0]}{item.master?.last_name?.[0]}</>
              )}
            </span>
            <span>{item.master?.first_name} {item.master?.last_name}</span>
          </div>
          <MasterRating masterId={item.master_id || item.master?.id}/>
        </div>
        {location && <div className="muted-line offering-address"><Icon name="pin" size={16}/><span><b>Место оказания:</b> {location}</span></div>}
        <div className={`price-row ${hasDiscount ? "has-discount" : ""}`}>
          <div className="catalog-price-stack">
            {hasDiscount && <span className="old-price">{formatMoney(item.price)}</span>}
            <b>{formatMoney(finalPrice)}</b>
          </div>
          <span>{hasDiscount ? `Скидка ${discountPercent}%` : "Стоимость услуги"}</span>
          {hasDiscount && <span className="discount-badge">−{discountPercent}%</span>}
          <Icon name="arrow" size={18}/>
        </div>
      </div>
    </article>
  );
}

function CatalogPage({ route }) {
  const { user } = useAuth();
  const queryString = route.split("?")[1] || "";
  const initial = useMemo(() => Object.fromEntries(new URLSearchParams(queryString)), [queryString]);
  const [filters, setFilters] = useState({ search: initial.search || "", category_id: initial.category_id || "", city_id: "", district_id: "", min_price: "", max_price: "", discounted_only: initial.discounted_only === "true", sort: initial.sort || "popular", page: 1, page_size: 9 });
  const [categories, setCategories] = useState([]);
  const [cities, setCities] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [data, setData] = useState({ items: [], total: 0, total_pages: 0, page: 1 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [viewerMasterId, setViewerMasterId] = useState(null);
  const [hideOwnOfferings, setHideOwnOfferings] = useState(false);
  useEffect(() => { endpoints.categories().then(setCategories).catch(() => {}); endpoints.cities().then(setCities).catch(() => {}); }, []);
  useEffect(() => {
    if (user?.role !== "master" || !user?.id) {
      setHideOwnOfferings(false);
      return;
    }
    setHideOwnOfferings(localStorage.getItem(`masterbooking_hide_own_offerings:${user.id}`) === "true");
  }, [user?.id, user?.role]);
  useEffect(() => {
    let mounted = true;
    if (user?.role !== "master") { setViewerMasterId(null); return undefined; }
    endpoints.masterMe().then((master) => { if (mounted) setViewerMasterId(master.id); }).catch(() => { if (mounted) setViewerMasterId(null); });
    return () => { mounted = false; };
  }, [user?.role]);
  useEffect(() => { if (!filters.city_id) { setDistricts([]); return; } endpoints.districts(filters.city_id).then(setDistricts).catch(() => setDistricts([])); }, [filters.city_id]);
  const offeringFilters = useMemo(() => ({
    ...filters,
    ...(hideOwnOfferings && viewerMasterId ? { exclude_master_id: viewerMasterId } : {}),
  }), [filters, hideOwnOfferings, viewerMasterId]);
  const load = useCallback(async () => { setLoading(true); setError(""); try { setData(await endpoints.offerings(offeringFilters)); } catch (e) { setError(safeError(e)); } finally { setLoading(false); } }, [offeringFilters]);
  useEffect(() => { const timer = setTimeout(load, 250); return () => clearTimeout(timer); }, [load]);
  const update = (key, value) => setFilters((prev) => ({ ...prev, [key]: value, page: key === "page" ? value : 1, ...(key === "city_id" ? { district_id: "" } : {}) }));
  const toggleOwnOfferings = (checked) => {
    setHideOwnOfferings(checked);
    if (user?.id) localStorage.setItem(`masterbooking_hide_own_offerings:${user.id}`, String(checked));
    setFilters((prev) => ({ ...prev, page: 1 }));
  };
  return (
    <section className="section catalog-section"><div className="container">
      <div className="page-heading"><span className="eyebrow">Каталог услуг</span><h1>Подберите услугу по вашим параметрам</h1><p>Сравнивайте предложения по направлению, стоимости и расположению мастера.</p></div>
      <div className="catalog-layout">
        <aside className="filter-panel">
          <div className="filter-title"><b>Параметры поиска</b><button onClick={() => setFilters({ search: "", category_id: "", city_id: "", district_id: "", min_price: "", max_price: "", discounted_only: false, sort: "popular", page: 1, page_size: 9 })}>Очистить</button></div>
          {user?.role === "master" && (
            <div className={`own-offerings-filter ${hideOwnOfferings ? "active" : ""}`}>
              <div className="own-offerings-filter-copy">
                <span className="own-filter-icon"><Icon name="briefcase" size={17}/></span>
                <div>
                  <b>Режим клиента</b>
                  <span>Скрывать мои услуги из результатов</span>
                </div>
              </div>
              <label className={`toggle-control ${!viewerMasterId ? "disabled" : ""}`} title={!viewerMasterId ? "Профиль мастера ещё загружается" : ""}>
                <input
                  type="checkbox"
                  checked={hideOwnOfferings}
                  disabled={!viewerMasterId}
                  onChange={(event) => toggleOwnOfferings(event.target.checked)}
                />
                <span className="toggle-track"><span className="toggle-knob" /></span>
              </label>
            </div>
          )}
          <Field label="Поиск по каталогу"><div className="input-with-icon"><Icon name="search" size={18}/><input value={filters.search} onChange={(e) => update("search", e.target.value)} placeholder="Введите название услуги" /></div></Field>
          <CategoryCascade categories={categories} value={filters.category_id} onChange={(categoryId) => update("category_id", categoryId)} allowAll />
          <Field label="Город"><select value={filters.city_id} onChange={(e) => update("city_id", e.target.value)}><option value="">Все города</option>{cities.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
          <Field label="Район"><select value={filters.district_id} onChange={(e) => update("district_id", e.target.value)} disabled={!filters.city_id}><option value="">Все районы</option>{districts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></Field>
          <Field label="Цена, ₽"><div className="split-inputs"><input type="number" min="1" value={filters.min_price} onChange={(e) => update("min_price", e.target.value)} placeholder="От"/><input type="number" min="1" value={filters.max_price} onChange={(e) => update("max_price", e.target.value)} placeholder="До"/></div></Field>
          <div className={`discount-offerings-filter ${filters.discounted_only ? "active" : ""}`}>
            <div className="discount-offerings-filter-copy">
              <span className="discount-filter-icon">%</span>
              <div>
                <b>Предложения со скидкой</b>
                <span>Показывать только услуги с действующей скидкой</span>
              </div>
            </div>
            <label className="toggle-control">
              <input
                type="checkbox"
                checked={Boolean(filters.discounted_only)}
                onChange={(event) => update("discounted_only", event.target.checked)}
              />
              <span className="toggle-track"><span className="toggle-knob" /></span>
            </label>
          </div>
        </aside>
        <div className="catalog-results">
          <div className="results-toolbar"><div><b>{loading ? "Обновляем результаты…" : `Найдено: ${data.total}`}</b><span>{hideOwnOfferings && viewerMasterId ? "ваши услуги исключены из выдачи" : "предложений по выбранным параметрам"}</span></div><select className="sort-select" value={filters.sort} onChange={(e) => update("sort", e.target.value)}><option value="popular">По популярности</option><option value="price_asc">Сначала дешевле</option><option value="price_desc">Сначала дороже</option></select></div>
          {error ? <InlineError text={error} retry={load}/> : loading ? <div className="offering-grid"><DemoOfferingSkeletons /></div> : data.items?.length ? <><div className="offering-grid">{data.items.map((item) => <OfferingCard key={item.id} item={item} isOwn={viewerMasterId === (item.master_id || item.master?.id)}/>)}</div><Pagination page={data.page} totalPages={data.total_pages} onPage={(page) => update("page", page)}/></> : <EmptyState title="Подходящих услуг не найдено" text="Измените параметры поиска или очистите часть фильтров." action="Очистить фильтры" onAction={() => setFilters({ search: "", category_id: "", city_id: "", district_id: "", min_price: "", max_price: "", discounted_only: false, sort: "popular", page: 1, page_size: 9 })}/>} 
        </div>
      </div>
    </div></section>
  );
}

function OfferingPage({ id }) {
  const { user } = useAuth();
  const notify = useToast();
  const [offering, setOffering] = useState(null);
  const [images, setImages] = useState([]);
  const [reviews, setReviews] = useState(null);
  const [date, setDate] = useState(todayIso());
  const [slots, setSlots] = useState([]);
  const [slot, setSlot] = useState("");
  const [loading, setLoading] = useState(true);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [booking, setBooking] = useState(false);
  const [error, setError] = useState("");
  const [viewerMasterId, setViewerMasterId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const item = await endpoints.offering(id);
      setOffering(item);
      const requests = [
        endpoints.offeringImages(id),
        endpoints.masterReviewsFull(item.master_id),
        user?.role === "master" ? endpoints.masterMe() : Promise.resolve(null),
      ];
      const [imgs, rev, ownMaster] = await Promise.allSettled(requests);
      if (imgs.status === "fulfilled") setImages(imgs.value);
      if (rev.status === "fulfilled") setReviews(rev.value);
      if (ownMaster.status === "fulfilled") setViewerMasterId(ownMaster.value?.id || null);
      else setViewerMasterId(null);
    } catch (e) { setError(safeError(e)); }
    finally { setLoading(false); }
  }, [id, user?.role]);
  useEffect(() => { load(); }, [load]);
  const isOwnOffering = Boolean(
    user?.role === "master"
    && viewerMasterId
    && offering
    && viewerMasterId === offering.master_id
  );

  useEffect(() => {
    if (!offering || !date || isOwnOffering) {
      setSlots([]);
      setSlot("");
      setSlotsLoading(false);
      return;
    }
    setSlotsLoading(true); setSlot("");
    endpoints.availableSlots(offering.master_id, offering.id, date).then((data) => setSlots(data.slots || [])).catch(() => setSlots([])).finally(() => setSlotsLoading(false));
  }, [offering, date, isOwnOffering]);

  const createBooking = async () => {
    if (!user) { go("/auth"); return; }
    if (isOwnOffering) { notify("Запись на собственную услугу недоступна", "error"); return; }
    if (!user.phone) { notify("Для записи укажите номер телефона в профиле", "error"); go("/profile"); return; }
    if (!slot) { notify("Выберите доступное время для записи", "error"); return; }
    setBooking(true);
    try {
      await endpoints.createBooking(offering.master_id, { offering_id: offering.id, booking_date: date, start_time: slot });
      notify("Запись создана. Детали доступны в личном кабинете");
      go(user.role === "master" ? "/master?tab=visits" : "/profile");
    } catch (e) { notify(safeError(e), "error"); }
    finally { setBooking(false); }
  };

  if (loading) return <PageLoader />;
  if (error) return <section className="section"><div className="container"><InlineError text={error} retry={load}/></div></section>;
  if (!offering) return null;
  const primary = images.find((i) => i.is_primary) || images[0];
  const otherImages = images.filter((i) => i.id !== primary?.id).slice(0, 3);
  return (
    <section className="section detail-section"><div className="container">
      <button className="back-link" onClick={() => history.back()}>← Вернуться в каталог</button>
      <div className="detail-grid">
        <div>
          <div className="detail-gallery">
            <div className="detail-main-image">{primary ? <img src={resolveMediaUrl(primary.image_url)} alt={offering.title}/> : <div className="image-fallback large"><Icon name="image" size={54}/><span>{offering.title.slice(0,1)}</span></div>}</div>
            {otherImages.length > 0 && <div className="detail-thumbs">{otherImages.map((img) => <img key={img.id} src={resolveMediaUrl(img.image_url)} alt="Фото услуги"/>)}</div>}
          </div>
          <div className="detail-copy"><div className="tag-row">{offering.tags?.map((tag) => <span className="tag" key={tag.id}>{tag.name}</span>)}</div><h1>{offering.title}</h1><p className="lead">{offering.description}</p><div className="detail-facts"><span><Icon name="clock"/> {offering.duration_minutes} минут</span><span><Icon name="pin"/> {[offering.master?.city, offering.master?.district, offering.master?.address].filter(Boolean).join(", ") || "Место оказания не указано"}</span></div></div>
          <MasterCard master={offering.master} reviews={reviews}/>
          <ReviewsBlock reviews={reviews}/>
        </div>
        <aside className="booking-card">
          <div className={`booking-price ${Number(offering.discount_percent || 0) > 0 ? "has-discount" : ""}`}>
            <small>Стоимость</small>
            <div className="booking-price-value">
              {Number(offering.discount_percent || 0) > 0 && <span className="old-price">{formatMoney(offering.price)}</span>}
              <b>{formatMoney(offering.final_price ?? offering.price)}</b>
              {Number(offering.discount_percent || 0) > 0 && <span className="discount-badge">−{Number(offering.discount_percent)}%</span>}
            </div>
            <span>за {offering.duration_minutes} мин</span>
          </div>
          {isOwnOffering ? (
            <>
              <div className="own-service-notice">
                <span className="own-service-notice-icon"><Icon name="briefcase" size={22}/></span>
                <div><b>Это ваша услуга</b><span>Записаться к самому себе нельзя. Выберите услугу другого мастера, чтобы оформить запись как клиент.</span></div>
              </div>
              <button className="button button-dark button-block" onClick={() => go("/master?tab=offerings")}>Управлять услугой</button>
              <button className="button button-ghost button-block" onClick={() => go("/catalog")}>Найти другого мастера</button>
            </>
          ) : (
            <>
              <Field label="Выберите дату"><input type="date" min={todayIso()} value={date} onChange={(e) => setDate(e.target.value)}/></Field>
              <div className="slot-block"><label>Свободное время</label>{slotsLoading ? <div className="mini-loader">Загружаем слоты…</div> : slots.length ? <div className="slots-grid">{slots.map((item) => <button className={slot === item ? "selected" : ""} key={item} onClick={() => setSlot(item)}>{item.slice(0,5)}</button>)}</div> : <div className="no-slots">На эту дату свободных слотов нет</div>}</div>
              <button className="button button-accent button-block" disabled={booking || !slot} onClick={createBooking}>{booking ? "Создаём запись…" : user ? "Записаться" : "Войти и записаться"}</button>
              <p className="booking-note">{user?.role === "master" ? "Запись появится в мастерской в разделе «Мои записи»." : "Подтверждение появится в разделе «Мои записи»."}</p>
            </>
          )}
        </aside>
      </div>
    </div></section>
  );
}

function MasterCard({ master, reviews }) {
  if (!master) return null;
  return <div className="master-card"><div className="master-avatar">{master.avatar_url ? <img src={resolveMediaUrl(master.avatar_url)} alt={`${master.first_name} ${master.last_name}`}/> : <span>{master.first_name?.[0]}{master.last_name?.[0]}</span>}</div><div className="master-card-main"><small>Ваш мастер</small><h3>{master.first_name} {master.last_name}</h3><div className="master-meta">{reviews && <span className="rating"><Icon name="star" size={17}/>{Number(reviews.average_rating || 0).toFixed(1)} · {reviews.reviews_count} отзывов</span>}</div></div>{master.phone && <a className="button button-ghost button-small" href={`tel:${master.phone}`}>Позвонить</a>}</div>;
}

function ReviewsBlock({ reviews }) {
  if (!reviews) return null;
  return <div className="reviews-section"><div className="reviews-heading"><div><span className="eyebrow">Отзывы</span><h2>{reviews.reviews_count ? `${Number(reviews.average_rating).toFixed(1)} из 5` : "Пока нет отзывов"}</h2></div>{reviews.reviews_count > 0 && <div className="rating-big"><Icon name="star" size={24}/><b>{Number(reviews.average_rating).toFixed(1)}</b><span>{reviews.reviews_count} отзывов</span></div>}</div><div className="review-list">{reviews.reviews?.slice(0,6).map((r) => <div className="review-card" key={r.id}><div className="review-top"><div className="avatar avatar-sm">{r.client_name?.[0] || "К"}</div><div><b>{r.client_name}</b><span>{formatDate(r.created_at)}</span></div><div className="stars">{"★".repeat(r.rating)}{"☆".repeat(5-r.rating)}</div></div>{r.comment && <p>{r.comment}</p>}</div>)}</div></div>;
}

function AuthPage() {
  const { user, login, register } = useAuth();
  const notify = useToast();
  const [mode, setMode] = useState("login");
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", first_name: "", last_name: "", phone: "" });
  const [message, setMessage] = useState("");
  useEffect(() => { if (user) go(user.role === "master" ? "/master" : user.role === "admin" ? "/admin" : "/profile"); }, [user]);
  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setMessage("");
    try {
      if (mode === "login") await login(form.email, form.password);
      else if (mode === "register") await register({ ...form, phone: form.phone || null });
      else if (mode === "forgot") { const res = await endpoints.forgotPassword(form.email); setMessage(res.message); }
      notify(mode === "register" ? "Аккаунт создан" : mode === "login" ? "Вход выполнен" : "Инструкции отправлены на email");
    } catch (e2) { setMessage(safeError(e2)); }
    finally { setLoading(false); }
  };
  return <section className="auth-section"><div className="auth-art"><div className="auth-art-content"><span className="eyebrow light">MasterBooking</span><h1>Запись к мастерам без лишних действий.</h1><p>Выбирайте услугу и доступное время онлайн, а все детали визита храните в личном кабинете.</p><div className="auth-quote">Поиск, запись и управление визитами — в одном сервисе.<span>MasterBooking</span></div></div></div><div className="auth-panel"><div className="auth-box"><button className="brand auth-brand" onClick={() => go("/")}><span className="brand-mark"><Icon name="logo" size={32}/></span><span>MasterBooking</span></button><span className="eyebrow">{mode === "register" ? "Регистрация" : mode === "forgot" ? "Восстановление доступа" : "Вход в аккаунт"}</span><h2>{mode === "register" ? "Создайте аккаунт" : mode === "forgot" ? "Восстановите доступ" : "Войдите в MasterBooking"}</h2><p>{mode === "register" ? "После регистрации вы сможете создавать записи, отслеживать их статус и оставлять отзывы." : mode === "forgot" ? "Укажите email, связанный с аккаунтом. Если он найден, мы отправим инструкции по восстановлению." : "Введите email и пароль, которые вы использовали при регистрации."}</p><form onSubmit={submit} className="auth-form">{mode === "register" && <div className="two-col"><Field label="Имя"><input required minLength="2" value={form.first_name} onChange={(e)=>setForm({...form, first_name:e.target.value})}/></Field><Field label="Фамилия"><input required minLength="2" value={form.last_name} onChange={(e)=>setForm({...form, last_name:e.target.value})}/></Field></div>}<Field label="Email"><input required type="email" value={form.email} onChange={(e)=>setForm({...form, email:e.target.value})} placeholder="you@example.com"/></Field>{mode !== "forgot" && <Field label="Пароль"><input required type="password" minLength={mode === "register" ? 8 : 1} value={form.password} onChange={(e)=>setForm({...form, password:e.target.value})} placeholder={mode === "register" ? "Не менее 8 символов" : "Введите пароль"}/></Field>}{mode === "register" && <Field label="Телефон"><input value={form.phone} onChange={(e)=>setForm({...form, phone:e.target.value})} placeholder="+7 999 123-45-67"/></Field>}{message && <div className={`form-message ${message.includes("ошиб") || message.includes("Невер") ? "error" : ""}`}>{message}</div>}<button className="button button-dark button-block" disabled={loading}>{loading ? "Выполняем запрос…" : mode === "register" ? "Создать аккаунт" : mode === "forgot" ? "Отправить инструкцию" : "Войти"}</button></form><div className="auth-links">{mode === "login" && <button onClick={()=>setMode("forgot")}>Забыли пароль?</button>}<button onClick={()=>{setMessage("");setMode(mode === "register" ? "login" : "register")}}>{mode === "register" ? "Уже зарегистрированы? Войти" : "Создать аккаунт"}</button>{mode === "forgot" && <button onClick={()=>setMode("login")}>Вернуться ко входу</button>}</div></div></div></section>;
}

function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const notify = useToast();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ first_name: user?.first_name || "", last_name: user?.last_name || "", phone: user?.phone || "" });
  const [editing, setEditing] = useState(false);
  const [reviewing, setReviewing] = useState(null);
  const [review, setReview] = useState({ rating: 5, comment: "" });
  const loadBookings = useCallback(async () => { try { setBookings(await endpoints.myBookings()); } catch(e){ notify(safeError(e), "error"); } finally { setLoading(false); } }, [notify]);
  useEffect(() => { loadBookings(); }, [loadBookings]);
  const saveProfile = async (e) => { e.preventDefault(); try { await endpoints.updateMe({ ...form, phone: form.phone || null }); await refreshUser(); setEditing(false); notify("Личные данные обновлены"); } catch(e2){ notify(safeError(e2), "error"); } };
  const cancel = async (id) => { try { await endpoints.cancelBooking(id); notify("Запись отменена"); loadBookings(); } catch(e){ notify(safeError(e), "error"); } };
  const submitReview = async (e) => {
    e.preventDefault();
    if (!reviewing) return;
    const bookingId = reviewing.id;
    try {
      await endpoints.createReview(bookingId, { rating: Number(review.rating), comment: review.comment || null });
      setBookings((current) => current.map((booking) => booking.id === bookingId ? { ...booking, has_review: true } : booking));
      notify("Спасибо. Отзыв опубликован");
      setReviewing(null);
      setReview({rating:5, comment:""});
    } catch(err){
      notify(safeError(err), "error");
    }
  };
  return <section className="section dashboard-section"><div className="container dashboard-layout"><aside className="profile-sidebar"><div className="profile-card"><AvatarManager compact/><h3>{user.first_name} {user.last_name}</h3><span>{user.email}</span><span className="role-badge">{user.role === "master" ? "Мастер" : user.role === "admin" ? "Администратор" : "Клиент"}</span></div><div className="side-menu"><button className="active"><Icon name="calendar"/>Мои записи</button><button onClick={()=>setEditing(true)}><Icon name="user"/>Личные данные</button>{user.role === "client" && <button onClick={()=>go("/become-master")}><Icon name="briefcase"/>Стать мастером</button>}</div></aside><div className="dashboard-main"><div className="dashboard-heading"><div><span className="eyebrow">Личный кабинет</span><h1>Мои записи</h1><p>Просматривайте предстоящие и завершённые визиты, следите за статусами и управляйте записями.</p></div><button className="button button-dark" onClick={()=>go("/catalog")}>Открыть каталог</button></div>{loading ? <PanelLoader/> : bookings.length ? <div className="booking-list">{bookings.map((b)=><BookingRow key={b.id} booking={b} onCancel={cancel} onReview={user.role === "master" ? undefined : ()=>setReviewing(b)}/>)}</div> : <EmptyState title="Записей пока нет" text="Откройте каталог, выберите услугу и подходящее свободное время." action="Открыть каталог" onAction={()=>go("/catalog")}/>}</div></div>{editing && <Modal title="Редактирование профиля" onClose={()=>setEditing(false)}><form onSubmit={saveProfile}><div className="two-col"><Field label="Имя"><input required value={form.first_name} onChange={(e)=>setForm({...form,first_name:e.target.value})}/></Field><Field label="Фамилия"><input required value={form.last_name} onChange={(e)=>setForm({...form,last_name:e.target.value})}/></Field></div><Field label="Телефон"><input value={form.phone} onChange={(e)=>setForm({...form,phone:e.target.value})}/></Field><button className="button button-dark button-block">Сохранить изменения</button></form></Modal>}{reviewing && <Modal title="Отзыв о визите" onClose={()=>setReviewing(null)}><form onSubmit={submitReview}><Field label="Оценка"><div className="rating-picker">{[1,2,3,4,5].map((n)=><button type="button" key={n} className={n<=review.rating?"active":""} onClick={()=>setReview({...review,rating:n})}>★</button>)}</div></Field><Field label="Комментарий"><textarea maxLength="1000" rows="5" value={review.comment} onChange={(e)=>setReview({...review,comment:e.target.value})} placeholder="Расскажите о качестве услуги и вашем впечатлении"/></Field><button className="button button-dark button-block">Опубликовать отзыв</button></form></Modal>}</section>;
}

function AvatarManager({ compact = false }) {
  const { user, avatarUrl, setUploadedAvatar, clearUploadedAvatar, refreshUser } = useAuth();
  const notify = useToast();
  const [busy, setBusy] = useState(false);

  const upload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const data = await endpoints.uploadAvatar(file);
      setUploadedAvatar(data.avatar_url);
      await refreshUser();
      notify("Аватар обновлён");
    } catch (error) {
      notify(safeError(error), "error");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  };

  const remove = async () => {
    if (!avatarUrl || busy) return;
    if (!window.confirm("Удалить аватар? Вместо фотографии будут показаны инициалы.")) return;
    setBusy(true);
    try {
      await endpoints.deleteAvatar();
      clearUploadedAvatar();
      await refreshUser();
      notify("Аватар удалён");
    } catch (error) {
      notify(safeError(error), "error");
    } finally {
      setBusy(false);
    }
  };

  return <div className={`avatar-manager ${compact ? "compact" : ""}`}>
    {!compact && <div className="avatar-manager-copy"><b>Аватар профиля</b><span>Эту фотографию видят клиенты рядом с вашим именем и услугами.</span></div>}
    <div className="avatar-manager-body">
      <span className={`avatar ${compact ? "avatar-xl" : "avatar-profile-edit"}`}>{avatarUrl ? <img src={avatarUrl} alt={`${user.first_name} ${user.last_name}`}/> : <>{user.first_name?.[0]}{user.last_name?.[0]}</>}</span>
      <div className="avatar-manager-actions">
        <label className={`button ${compact ? "button-ghost button-small" : "button-dark button-small"} avatar-file-button ${busy ? "disabled" : ""}`}>
          <Icon name="image" size={15}/>{busy ? "Подождите…" : avatarUrl ? "Сменить фото" : "Загрузить фото"}
          <input disabled={busy} type="file" accept="image/jpeg,image/png,image/webp" onChange={upload}/>
        </label>
        {avatarUrl && <button type="button" className="button button-ghost button-small avatar-delete-button" disabled={busy} onClick={remove}><Icon name="trash" size={14}/>Удалить</button>}
      </div>
    </div>
  </div>;
}

function BookingRow({ booking, onCancel, onReview }) {
  const canCancel = ["pending", "confirmed"].includes(booking.status);
  const canReview = booking.status === "completed" && !booking.has_review && Boolean(onReview);
  const reviewCompleted = booking.status === "completed" && booking.has_review;
  return <div className="booking-row"><div className="booking-date-box"><b>{new Date(booking.booking_date).getDate()}</b><span>{new Intl.DateTimeFormat("ru-RU",{month:"short"}).format(new Date(booking.booking_date))}</span></div><div className="booking-info"><span className={`status status-${booking.status}`}>{statusLabels[booking.status] || booking.status}</span><h3>Запись к мастеру</h3><div className="booking-meta"><span><Icon name="clock" size={16}/>{booking.start_time?.slice(0,5)}–{booking.end_time?.slice(0,5)}</span><span>ID: {booking.id.slice(0,8)}</span></div></div><div className="booking-actions">{canCancel && <button className="button button-ghost button-small" onClick={()=>onCancel(booking.id)}>Отменить</button>}{canReview && <button className="button button-dark button-small" onClick={onReview}>Оставить отзыв</button>}{reviewCompleted && <span className="review-complete-badge">★ Отзыв оставлен</span>}</div></div>;
}

function BecomeMasterPage() {
  const { user } = useAuth();
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    if (user?.role === "master") go("/master");
  }, [user?.role]);

  if (user?.role === "master") return <PageLoader/>;
  if (user?.role !== "client") return <AccessDenied/>;

  if (confirmed) {
    return <CreateMasterProfile onCreated={() => go("/master")} onCancel={() => setConfirmed(false)} />;
  }

  return (
    <section className="section become-master-section">
      <div className="container narrow-container">
        <div className="confirm-card">
          <div className="confirm-icon"><Icon name="briefcase" size={30}/></div>
          <span className="eyebrow">Переход в мастерскую</span>
          <h1>Стать мастером?</h1>
          <p>После создания профессионального профиля роль аккаунта изменится с «Клиент» на «Мастер». Вы получите доступ к услугам, расписанию, отзывам и записям клиентов.</p>
          <div className="confirm-note"><b>Важно</b><span>Сама кнопка ничего не меняет. Роль обновится только после того, как вы заполните форму и профиль мастера будет успешно создан на сервере.</span></div>
          <div className="confirm-actions">
            <button className="button button-ghost" onClick={() => go("/profile")}>Нет, вернуться</button>
            <button className="button button-dark" onClick={() => setConfirmed(true)}>Да, продолжить</button>
          </div>
        </div>
      </div>
    </section>
  );
}

function MasterDashboard({ route = "/master" }) {
  const { user, avatarUrl } = useAuth();
  const notify = useToast();
  const requestedTab = new URLSearchParams(route.split("?")[1] || "").get("tab");
  const allowedTabs = ["bookings", "visits", "offerings", "schedule", "reviews", "profile"];
  const [tab, setTab] = useState(allowedTabs.includes(requestedTab) ? requestedTab : "bookings");
  const [master, setMaster] = useState(null);
  const [missingProfile, setMissingProfile] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadMaster = useCallback(async()=>{setLoading(true);try{setMaster(await endpoints.masterMe());setMissingProfile(false);}catch(e){if(e.status===404)setMissingProfile(true);else notify(safeError(e),"error");}finally{setLoading(false)}},[notify]);
  useEffect(()=>{loadMaster()},[loadMaster]);
  useEffect(() => {
    const nextTab = new URLSearchParams(route.split("?")[1] || "").get("tab");
    if (allowedTabs.includes(nextTab)) setTab(nextTab);
  }, [route]);

  const openTab = (nextTab) => {
    setTab(nextTab);
    go(`/master?tab=${nextTab}`);
  };

  if (loading) return <PageLoader/>;
  if (missingProfile) return <CreateMasterProfile onCreated={loadMaster}/>;

  return <section className="section dashboard-section"><div className="container master-dashboard"><aside className="master-sidebar"><div className="master-side-profile"><span className="avatar avatar-lg">{avatarUrl ? <img src={avatarUrl} alt="Аватар"/> : <>{user.first_name?.[0]}{user.last_name?.[0]}</>}</span><div><b>{user.first_name} {user.last_name}</b><span>Профиль мастера</span></div></div><div className="side-menu">{[["bookings","calendar","Записи клиентов"],["visits","user","Мои записи"],["offerings","grid","Услуги"],["schedule","clock","Расписание"],["reviews","star","Отзывы"],["profile","user","Профиль"]].map(([id,icon,label])=><button key={id} className={tab===id?"active":""} onClick={()=>openTab(id)}><Icon name={icon}/>{label}</button>)}</div><button className="master-find-service" onClick={()=>go("/catalog")}><Icon name="search" size={17}/><span><b>Найти мастера</b><small>Записаться как клиент</small></span></button></aside><div className="dashboard-main">{tab==="bookings"&&<MasterBookings/>}{tab==="visits"&&<MasterPersonalBookings/>}{tab==="offerings"&&<MasterOfferings/>}{tab==="schedule"&&<MasterSchedule/>}{tab==="reviews"&&<MasterReviews/>}{tab==="profile"&&<MasterProfile master={master} onUpdated={loadMaster}/>}</div></div></section>;
}

function CreateMasterProfile({ onCreated, onCancel }) {
  const notify=useToast(); const { refreshUser } = useAuth(); const [cities,setCities]=useState([]); const [districts,setDistricts]=useState([]); const [form,setForm]=useState({description:"",experience:0,education:"",city_id:"",district_id:"",address:""}); const [loading,setLoading]=useState(false);
  useEffect(()=>{endpoints.cities().then(setCities).catch(()=>{})},[]); useEffect(()=>{if(form.city_id)endpoints.districts(form.city_id).then(setDistricts).catch(()=>setDistricts([]));else setDistricts([])},[form.city_id]);
  const submit=async(e)=>{e.preventDefault();setLoading(true);try{await endpoints.createMasterProfile({...form,experience:Number(form.experience),city_id:form.city_id||null,district_id:form.district_id||null,address:form.address||null});notify("Профиль мастера создан");await refreshUser();onCreated();}catch(err){notify(safeError(err),"error")}finally{setLoading(false)}};
  return <section className="section"><div className="container narrow-container"><div className="form-card"><span className="eyebrow">Новый этап</span><h1>Создайте профиль мастера</h1><p>Основные данные возьмём из вашего аккаунта. Здесь укажите профессиональную информацию и место работы.</p><form onSubmit={submit}><Field label="О себе"><textarea required minLength="10" maxLength="2000" rows="5" value={form.description} onChange={(e)=>setForm({...form,description:e.target.value})} placeholder="Расскажите о специализации, подходе и опыте"/></Field><div className="two-col"><Field label="Опыт работы, лет"><input type="number" min="0" required value={form.experience} onChange={(e)=>setForm({...form,experience:e.target.value})}/></Field><Field label="Образование"><input required minLength="2" value={form.education} onChange={(e)=>setForm({...form,education:e.target.value})}/></Field></div><div className="two-col"><Field label="Город"><select value={form.city_id} onChange={(e)=>setForm({...form,city_id:e.target.value,district_id:""})}><option value="">Не выбран</option>{cities.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></Field><Field label="Район"><select value={form.district_id} onChange={(e)=>setForm({...form,district_id:e.target.value})} disabled={!form.city_id}><option value="">Не выбран</option>{districts.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></Field></div><Field label="Адрес приёма"><input maxLength="255" value={form.address} onChange={(e)=>setForm({...form,address:e.target.value})} placeholder="Улица, дом, помещение"/></Field><div className="form-actions">{onCancel&&<button type="button" className="button button-ghost" onClick={onCancel} disabled={loading}>Назад</button>}<button className="button button-dark" disabled={loading}>{loading?"Создаём…":"Создать профиль мастера"}</button></div></form></div></div></section>;
}

function DashboardHeader({ eyebrow, title, text, action, onAction, actionIcon = "plus" }) { return <div className="dashboard-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{text}</p></div>{action&&<button className="button button-dark" onClick={onAction}><Icon name={actionIcon} size={18}/>{action}</button>}</div>; }

function MasterBookings(){const notify=useToast();const[date,setDate]=useState(todayIso());const[items,setItems]=useState([]);const[loading,setLoading]=useState(true);const load=useCallback(async()=>{setLoading(true);try{setItems(await endpoints.masterBookings(date))}catch(e){notify(safeError(e),"error")}finally{setLoading(false)}},[date,notify]);useEffect(()=>{load()},[load]);const change=async(id,status)=>{try{await endpoints.updateBookingStatus(id,status);notify("Статус обновлён");load()}catch(e){notify(safeError(e),"error")}};return <><DashboardHeader eyebrow="Приём клиентов" title="Записи клиентов" text="Просматривайте записи на выбранную дату, контактные данные клиентов и актуальный статус визита."/><div className="toolbar-card"><Field label="Дата"><input type="date" value={date} onChange={(e)=>setDate(e.target.value)}/></Field><div className="toolbar-stat"><b>{items.length}</b><span>записей на выбранную дату</span></div></div>{loading?<PanelLoader/>:items.length?<div className="booking-list">{items.map(b=><div className="booking-row master-booking" key={b.id}><div className="time-box">{b.start_time?.slice(0,5)}</div><div className="booking-info"><span className={`status status-${b.status}`}>{statusLabels[b.status]}</span><h3>{b.client_name}</h3><div className="booking-meta"><span>{b.client_phone}</span>{b.client_email&&<span>{b.client_email}</span>}</div></div><select className="status-select" value={b.status} onChange={(e)=>change(b.id,e.target.value)} disabled={b.status==="cancelled"}><option value="pending">Ожидает</option><option value="confirmed">Подтверждено</option><option value="completed">Завершено</option><option value="cancelled">Отменено</option></select></div>)}</div>:<EmptyState title="На выбранную дату записей нет" text="Выберите другую дату, чтобы проверить расписание."/>}</>}

function MasterPersonalBookings() {
  const notify = useToast();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(null);
  const [review, setReview] = useState({ rating: 5, comment: "" });

  const load = useCallback(async () => {
    setLoading(true);
    try { setBookings(await endpoints.myBookings()); }
    catch (error) { notify(safeError(error), "error"); }
    finally { setLoading(false); }
  }, [notify]);

  useEffect(() => { load(); }, [load]);

  const cancel = async (id) => {
    try {
      await endpoints.cancelBooking(id);
      notify("Запись отменена");
      load();
    } catch (error) { notify(safeError(error), "error"); }
  };

  const submitReview = async (event) => {
    event.preventDefault();
    if (!reviewing) return;

    try {
      await endpoints.createReview(reviewing.id, {
        rating: Number(review.rating),
        comment: review.comment || null,
      });
      const bookingId = reviewing.id;
      setBookings((current) => current.map((booking) => booking.id === bookingId ? { ...booking, has_review: true } : booking));
      notify("Спасибо. Отзыв опубликован");
      setReviewing(null);
      setReview({ rating: 5, comment: "" });
    } catch (error) {
      notify(safeError(error), "error");
    }
  };

  const closeReview = () => {
    setReviewing(null);
    setReview({ rating: 5, comment: "" });
  };

  return <>
    <DashboardHeader
      eyebrow="Личные визиты"
      title="Мои записи к другим мастерам"
      text="Здесь отображаются ваши записи как клиента. Записи клиентов к вашим услугам находятся в отдельном разделе кабинета мастера."
      action="Найти услугу"
      actionIcon="search"
      onAction={() => go("/catalog")}
    />
    <div className="master-client-mode-note"><Icon name="user" size={20}/><div><b>Режим клиента</b><span>Ваш профиль мастера остаётся активным. Здесь можно записываться к другим специалистам, отменять визиты и публиковать отзывы.</span></div></div>
    {loading ? <PanelLoader/> : bookings.length ? (
      <div className="booking-list">{bookings.map((booking) => (
        <BookingRow
          key={booking.id}
          booking={booking}
          onCancel={cancel}
          onReview={() => setReviewing(booking)}
        />
      ))}</div>
    ) : <EmptyState title="Личных записей пока нет" text="Откройте каталог и выберите услугу другого специалиста." action="Открыть каталог" onAction={() => go("/catalog")}/>}

    {reviewing && <Modal title="Отзыв о визите" onClose={closeReview}>
      <form onSubmit={submitReview}>
        <div className="review-booking-context">
          <Icon name="calendar" size={18}/>
          <div><b>Завершённый визит</b><span>{formatDate(reviewing.booking_date)} · {reviewing.start_time?.slice(0,5)}</span></div>
        </div>
        <Field label="Оценка">
          <div className="rating-picker">{[1,2,3,4,5].map((number) => (
            <button
              type="button"
              key={number}
              className={number <= review.rating ? "active" : ""}
              onClick={() => setReview({ ...review, rating: number })}
              aria-label={`Оценка ${number}`}
            >★</button>
          ))}</div>
        </Field>
        <Field label="Комментарий">
          <textarea
            maxLength="1000"
            rows="5"
            value={review.comment}
            onChange={(event) => setReview({ ...review, comment: event.target.value })}
            placeholder="Поделитесь впечатлением о визите"
          />
        </Field>
        <button className="button button-dark button-block">Опубликовать отзыв</button>
      </form>
    </Modal>}
  </>;
}

function MasterOfferings() {
  const notify = useToast();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState(null);
  const [photosFor, setPhotosFor] = useState(null);
  const [photoVersion, setPhotoVersion] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    try { setItems(await endpoints.myOfferings()); }
    catch (error) { notify(safeError(error), "error"); }
    finally { setLoading(false); }
  }, [notify]);

  useEffect(() => { load(); }, [load]);

  const remove = async (id) => {
    if (!confirm("Удалить услугу без возможности восстановления?")) return;
    try {
      await endpoints.deleteOffering(id);
      notify("Услуга удалена из каталога");
      load();
    } catch (error) { notify(safeError(error), "error"); }
  };

  const photosChanged = () => {
    setPhotoVersion((version) => version + 1);
    load();
  };

  return <>
    <DashboardHeader eyebrow="Услуги и цены" title="Мои услуги" text="Публикуйте услуги, настраивайте стоимость и продолжительность, управляйте фотографиями и тегами." action="Добавить услугу" onAction={() => setCreating(true)}/>
    {loading ? <PanelLoader/> : items.length ? (
      <div className="service-list">{items.map((item) => (
        <div className="service-row" key={item.id}>
          <div className="service-row-image"><OfferingImage key={`${item.id}-${photoVersion}`} offeringId={item.id} alt={item.title}/></div>
          <div className="service-row-main">
            <div className="tag-row">{item.tags?.slice(0,3).map((tag) => <span className="tag" key={tag.id}>{tag.name}</span>)}</div>
            <h3>{item.title}</h3>
            <span>{item.duration_minutes} мин · {item.is_active ? "Активна" : "Скрыта"}</span>
          </div>
          <div className="service-price-block">
            {Number(item.discount_percent || 0) > 0 && <span className="old-price">{formatMoney(item.price)}</span>}
            <b className="service-price">{formatMoney(item.final_price ?? item.price)}</b>
            {Number(item.discount_percent || 0) > 0 && <span className="service-discount">−{Number(item.discount_percent)}%</span>}
          </div>
          <div className="row-actions">
            <button className="photo-manage-button" type="button" onClick={() => setPhotosFor(item)}><Icon name="image" size={17}/><span>Фото</span></button>
            <button className="icon-button" title="Редактировать" onClick={() => setEditing(item)}><Icon name="edit"/></button>
            <button className="icon-button danger" title="Удалить" onClick={() => remove(item.id)}><Icon name="trash"/></button>
          </div>
        </div>
      ))}</div>
    ) : <EmptyState title="Услуги пока не опубликованы" text="Добавьте первую услугу, чтобы она появилась в каталоге и стала доступна клиентам." action="Добавить услугу" onAction={() => setCreating(true)}/>}

    {(creating || editing) && <OfferingForm item={editing} onClose={() => { setCreating(false); setEditing(null); }} onSaved={() => { setCreating(false); setEditing(null); photosChanged(); }}/>} 
    {photosFor && <OfferingPhotosModal item={photosFor} onClose={() => setPhotosFor(null)} onChanged={photosChanged}/>} 
  </>;
}

function OfferingPhotosModal({ item, onClose, onChanged }) {
  const notify = useToast();
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setImages(await endpoints.offeringImages(item.id)); }
    catch (error) { notify(safeError(error), "error"); }
    finally { setLoading(false); }
  }, [item.id, notify]);

  useEffect(() => { load(); }, [load]);

  const upload = async (event) => {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (!files.length) return;
    setUploading(true);
    try {
      for (const file of files) await endpoints.uploadOfferingImage(item.id, file);
      notify(files.length === 1 ? "Фотография добавлена" : `Добавлено фотографий: ${files.length}`);
      await load();
      onChanged();
    } catch (error) { notify(safeError(error), "error"); }
    finally { setUploading(false); }
  };

  const makePrimary = async (imageId) => {
    try {
      await endpoints.setPrimaryImage(item.id, imageId);
      notify("Основная фотография изменена");
      await load();
      onChanged();
    } catch (error) { notify(safeError(error), "error"); }
  };

  const remove = async (imageId) => {
    if (!confirm("Удалить эту фотографию?")) return;
    try {
      await endpoints.deleteOfferingImage(item.id, imageId);
      notify("Фотография удалена");
      await load();
      onChanged();
    } catch (error) { notify(safeError(error), "error"); }
  };

  return <Modal title={`Фотографии · ${item.title}`} onClose={onClose} wide>
    <div className="photo-manager-head">
      <div><b>Фотогалерея услуги</b><span>До 20 фотографий. Основная показывается первой в каталоге.</span></div>
      <label className={`button button-dark photo-upload-button ${uploading ? "disabled" : ""}`}>
        <Icon name="plus" size={16}/>{uploading ? "Загрузка…" : "Добавить фото"}
        <input type="file" multiple disabled={uploading} accept="image/jpeg,image/png,image/webp" onChange={upload}/>
      </label>
    </div>
    {loading ? <PanelLoader/> : images.length ? (
      <div className="photo-manager-grid">{images.map((image) => (
        <div className={`photo-manager-item ${image.is_primary ? "primary" : ""}`} key={image.id}>
          <img src={resolveMediaUrl(image.image_url)} alt={item.title}/>
          {image.is_primary && <span className="primary-photo-badge"><Icon name="star" size={13}/>Основная</span>}
          <div className="photo-manager-actions">
            {!image.is_primary && <button type="button" className="button button-light button-small" onClick={() => makePrimary(image.id)}>Сделать основной</button>}
            <button type="button" className="icon-button danger" title="Удалить фотографию" onClick={() => remove(image.id)}><Icon name="trash" size={17}/></button>
          </div>
        </div>
      ))}</div>
    ) : <div className="photo-manager-empty"><Icon name="image" size={38}/><b>Фотографий пока нет</b><span>Загрузите первую фотографию — backend автоматически сделает её основной.</span></div>}
  </Modal>;
}

function OfferingForm({ item, onClose, onSaved }) {
  const notify = useToast();
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);
  const [form, setForm] = useState({
    title: item?.title || "",
    description: item?.description || "",
    price: item?.price || "",
    discount_percent: item?.discount_percent ?? 0,
    duration_minutes: item?.duration_minutes || 60,
    category_id: item?.category_id || "",
    tag_ids: item?.tags?.map((tag) => tag.id) || [],
  });
  const [loading, setLoading] = useState(false);
  const [primaryPhoto, setPrimaryPhoto] = useState(null);
  const [galleryPhotos, setGalleryPhotos] = useState([]);
  const primaryPreview = useMemo(() => primaryPhoto ? URL.createObjectURL(primaryPhoto) : null, [primaryPhoto]);
  const galleryPreviews = useMemo(() => galleryPhotos.map((file) => ({ file, url: URL.createObjectURL(file) })), [galleryPhotos]);

  useEffect(() => () => { if (primaryPreview) URL.revokeObjectURL(primaryPreview); }, [primaryPreview]);
  useEffect(() => () => { galleryPreviews.forEach(({ url }) => URL.revokeObjectURL(url)); }, [galleryPreviews]);

  useEffect(() => {
    endpoints.categories().then(setCategories).catch(() => {});
    endpoints.tags().then(setTags).catch(() => {});
  }, []);

  const toggleTag = (id) => setForm((previous) => ({
    ...previous,
    tag_ids: previous.tag_ids.includes(id)
      ? previous.tag_ids.filter((tagId) => tagId !== id)
      : [...previous.tag_ids, id].slice(0, 10),
  }));

  const choosePrimary = (event) => {
    const file = event.target.files?.[0] || null;
    setPrimaryPhoto(file);
    if (file) setGalleryPhotos((previous) => previous.slice(0, 19));
    event.target.value = "";
  };

  const addGalleryPhotos = (event) => {
    const incoming = Array.from(event.target.files || []);
    if (!incoming.length) return;
    const limit = primaryPhoto ? 19 : 20;
    setGalleryPhotos((previous) => {
      const next = [...previous, ...incoming].slice(0, limit);
      if (previous.length + incoming.length > limit) {
        notify(`Для одной услуги можно выбрать максимум ${primaryPhoto ? "19 фото галереи + 1 основное" : "20 фотографий"}.`, "error");
      }
      return next;
    });
    event.target.value = "";
  };

  const removeGalleryPhoto = (index) => {
    setGalleryPhotos((previous) => previous.filter((_, photoIndex) => photoIndex !== index));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!form.category_id) {
      notify("Выберите подкатегорию услуги", "error");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...form,
        price: Number(form.price),
        discount_percent: Number(form.discount_percent || 0),
        duration_minutes: Number(form.duration_minutes),
      };
      if (item) {
        await endpoints.updateOffering(item.id, payload);
        notify("Услуга обновлена");
      } else {
        const created = await endpoints.createOffering(payload);
        const photos = [primaryPhoto, ...galleryPhotos].filter(Boolean);
        let uploaded = 0;
        const failed = [];

        for (const photo of photos) {
          try {
            await endpoints.uploadOfferingImage(created.id, photo);
            uploaded += 1;
          } catch (photoError) {
            failed.push(photo.name);
          }
        }

        if (!photos.length) {
          notify("Услуга создана");
        } else if (!failed.length) {
          notify(`Услуга создана · загружено фотографий: ${uploaded}`);
        } else {
          notify(`Услуга создана. Загружено ${uploaded} из ${photos.length} фотографий.`, "error");
        }
      }
      onSaved();
    } catch (err) {
      notify(safeError(err), "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={item ? "Редактировать услугу" : "Новая услуга"} onClose={onClose} wide>
      <form onSubmit={submit}>
        <Field label="Название"><input required minLength="2" maxLength="100" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })}/></Field>
        <Field label="Описание услуги"><textarea required rows="5" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })}/></Field>
        <div className="three-col offering-price-fields">
          <Field label="Базовая цена, ₽"><input required type="number" min="1" step="0.01" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })}/></Field>
          <Field label="Скидка, %"><input type="number" min="0" max="100" step="1" value={form.discount_percent} onChange={(event) => setForm({ ...form, discount_percent: event.target.value })}/></Field>
          <Field label="Длительность, мин"><input required type="number" min="1" value={form.duration_minutes} onChange={(event) => setForm({ ...form, duration_minutes: event.target.value })}/></Field>
        </div>
        {Number(form.discount_percent || 0) > 0 && Number(form.price || 0) > 0 && (
          <div className="discount-preview">
            <span className="discount-preview-badge">−{Number(form.discount_percent)}%</span>
            <div><small>Цена для клиента</small><b>{formatMoney(Number(form.price) * (100 - Number(form.discount_percent)) / 100)}</b></div>
            <span className="discount-preview-old">{formatMoney(form.price)}</span>
          </div>
        )}
        <div className="offering-category-block">
          <div className="offering-category-copy">
            <b>Категория услуги</b>
            <span>Сначала выберите основное направление, затем точную подкатегорию.</span>
          </div>
          <CategoryCascade
            categories={categories}
            value={form.category_id}
            onChange={(categoryId) => setForm((previous) => ({ ...previous, category_id: categoryId }))}
            requireLeaf
          />
        </div>
        {!item && <div className="new-offering-media">
          <div className="new-offering-media-heading">
            <div><b>Фотографии услуги</b><span>Основная фотография загружается первой. Затем можно сразу добавить галерею — всего до 20 изображений.</span></div>
            <span className="photo-counter">{(primaryPhoto ? 1 : 0) + galleryPhotos.length}/20</span>
          </div>
          <div className="new-offering-media-grid">
            <div className="new-offering-photo primary-picker-card">
              <div className="new-offering-photo-copy"><b>Основная фотография</b><span>Будет первой в каталоге и на странице услуги.</span></div>
              <label className="new-offering-photo-picker">
                {primaryPreview ? <img src={primaryPreview} alt="Предпросмотр основной фотографии"/> : <div><Icon name="star" size={25}/><b>Выбрать основную</b><span>JPEG, PNG или WEBP · до 5 МБ</span></div>}
                <input type="file" accept="image/jpeg,image/png,image/webp" onChange={choosePrimary}/>
              </label>
              {primaryPhoto && <div className="selected-photo-footer"><span title={primaryPhoto.name}>{primaryPhoto.name}</span><button className="text-link remove-selected-photo" type="button" onClick={() => setPrimaryPhoto(null)}>Убрать</button></div>}
            </div>
            <div className="new-offering-gallery">
              <div className="new-offering-photo-copy"><b>Фотогалерея</b><span>Выберите сразу несколько дополнительных фотографий.</span></div>
              <label className="gallery-upload-dropzone">
                <Icon name="plus" size={24}/><b>Добавить фото в галерею</b><span>Можно выбрать несколько файлов одновременно</span>
                <input type="file" multiple accept="image/jpeg,image/png,image/webp" onChange={addGalleryPhotos}/>
              </label>
              {galleryPreviews.length > 0 ? <div className="selected-gallery-grid">{galleryPreviews.map(({ file, url }, index) => <div className="selected-gallery-item" key={`${file.name}-${file.lastModified}-${index}`}><img src={url} alt={`Фото галереи ${index + 1}`}/><button type="button" title="Убрать фотографию" onClick={() => removeGalleryPhoto(index)}><Icon name="close" size={14}/></button><span>{index + 1}</span></div>)}</div> : <div className="gallery-empty-note">Дополнительные фотографии пока не выбраны.</div>}
            </div>
          </div>
        </div>}
        <Field label="Теги (до 10)"><div className="tag-picker">{tags.map((tag) => <button type="button" key={tag.id} className={form.tag_ids.includes(tag.id) ? "active" : ""} onClick={() => toggleTag(tag.id)}>{tag.name}</button>)}</div></Field>
        <button className="button button-dark button-block" disabled={loading}>{loading ? "Сохраняем и загружаем фото…" : "Сохранить услугу"}</button>
      </form>
    </Modal>
  );
}

function MasterSchedule(){const notify=useToast();const[items,setItems]=useState([]);const[loading,setLoading]=useState(true);const[editing,setEditing]=useState(null);const load=useCallback(async()=>{setLoading(true);try{setItems(await endpoints.mySchedules())}catch(e){notify(safeError(e),"error")}finally{setLoading(false)}},[notify]);useEffect(()=>{load()},[load]);const byDay=Object.fromEntries(items.map(i=>[i.day_of_week,i]));return <><DashboardHeader eyebrow="Рабочее расписание" title="График работы" text="Укажите рабочие дни и часы. На основе графика сервис рассчитает доступное время для клиентов."/>{loading?<PanelLoader/>:<div className="schedule-list">{weekDays.map(([id,label])=>{const item=byDay[id];return <div className="schedule-row" key={id}><div><b>{label}</b><span>{item?(item.is_working?`${item.start_time?.slice(0,5)} — ${item.end_time?.slice(0,5)}`:"Выходной"):"График не задан"}</span></div><span className={`schedule-dot ${item?.is_working?"on":""}`}></span><button className="button button-ghost button-small" onClick={()=>setEditing(item||{day_of_week:id,start_time:"09:00",end_time:"18:00",is_working:true})}>{item?"Изменить":"Настроить"}</button></div>})}</div>}{editing&&<ScheduleForm item={editing} exists={Boolean(editing.id)} onClose={()=>setEditing(null)} onSaved={()=>{setEditing(null);load()}}/>}</>}

function ScheduleForm({item,exists,onClose,onSaved}){const notify=useToast();const[form,setForm]=useState({start_time:item.start_time?.slice(0,5)||"09:00",end_time:item.end_time?.slice(0,5)||"18:00",is_working:item.is_working!==false});const dayLabel=weekDays.find(([id])=>id===item.day_of_week)?.[1]||item.day_of_week;const submit=async(e)=>{e.preventDefault();const data={day_of_week:item.day_of_week,is_working:form.is_working,start_time:form.is_working?form.start_time:null,end_time:form.is_working?form.end_time:null};try{if(exists)await endpoints.updateSchedule(item.id,data);else await endpoints.createSchedule(data);notify("График работы сохранён");onSaved()}catch(err){notify(safeError(err),"error")}};return <Modal title={`Настройка графика · ${dayLabel}`} onClose={onClose}><form onSubmit={submit}><div className="schedule-fixed-day"><span>День недели</span><b>{dayLabel}</b></div><label className="switch-row"><input type="checkbox" checked={form.is_working} onChange={(e)=>setForm({...form,is_working:e.target.checked})}/><span>Принимать записи в этот день</span></label>{form.is_working&&<div className="two-col"><Field label="Начало рабочего дня"><input type="time" value={form.start_time} onChange={(e)=>setForm({...form,start_time:e.target.value})}/></Field><Field label="Окончание рабочего дня"><input type="time" value={form.end_time} onChange={(e)=>setForm({...form,end_time:e.target.value})}/></Field></div>}<button className="button button-dark button-block">Сохранить</button></form></Modal>}

function MasterReviews(){const notify=useToast();const[items,setItems]=useState([]);const[loading,setLoading]=useState(true);useEffect(()=>{endpoints.myMasterReviews().then(setItems).catch(e=>notify(safeError(e),"error")).finally(()=>setLoading(false))},[notify]);const avg=items.length?items.reduce((s,r)=>s+r.rating,0)/items.length:0;return <><DashboardHeader eyebrow="Репутация" title="Отзывы клиентов" text="Отзывы публикуются после завершённых визитов и формируют рейтинг вашего профиля."/><div className="stats-grid"><div className="stat-card"><span>Средний рейтинг</span><b>{avg?avg.toFixed(1):"—"}</b><small>из 5</small></div><div className="stat-card"><span>Опубликовано отзывов</span><b>{items.length}</b><small>за весь период</small></div></div>{loading?<PanelLoader/>:items.length?<div className="review-list dashboard-reviews">{items.map(r=><div className="review-card" key={r.id}><div className="review-top"><div className="avatar avatar-sm">{r.client_name?.[0]||"К"}</div><div><b>{r.client_name}</b><span>{formatDate(r.created_at)}</span><span className="review-offering"><Icon name="briefcase" size={13}/><b>Услуга:</b> {r.offering_title}</span></div><div className="stars">{"★".repeat(r.rating)}{"☆".repeat(5-r.rating)}</div></div>{r.comment&&<p>{r.comment}</p>}</div>)}</div>:<EmptyState title="Отзывы пока не опубликованы" text="Первый отзыв появится после завершённого визита и оценки клиента."/>}</>}

function MasterProfile({master,onUpdated}){
  const notify=useToast();
  const[cities,setCities]=useState([]);
  const[districts,setDistricts]=useState([]);
  const[form,setForm]=useState({first_name:master.first_name,last_name:master.last_name,description:master.description,experience:master.experience,education:master.education,city_id:master.city_id||"",district_id:master.district_id||"",address:master.address||""});
  useEffect(()=>{endpoints.cities().then(setCities).catch(()=>{})},[]);
  useEffect(()=>{if(form.city_id)endpoints.districts(form.city_id).then(setDistricts).catch(()=>{});else setDistricts([]);},[form.city_id]);
  const submit=async(e)=>{e.preventDefault();try{await endpoints.updateMasterProfile({...form,experience:Number(form.experience),city_id:form.city_id||null,district_id:form.district_id||null,address:form.address||null});notify("Профиль мастера обновлён");onUpdated()}catch(err){notify(safeError(err),"error")}};
  return <><DashboardHeader eyebrow="Публичный профиль" title="Профиль мастера" text="Эта информация отображается клиентам в каталоге и на страницах ваших услуг."/><div className="form-card flat master-profile-card"><AvatarManager/><div className="profile-section-divider"/><form onSubmit={submit}><div className="two-col"><Field label="Имя"><input value={form.first_name} onChange={(e)=>setForm({...form,first_name:e.target.value})}/></Field><Field label="Фамилия"><input value={form.last_name} onChange={(e)=>setForm({...form,last_name:e.target.value})}/></Field></div><Field label="О мастере"><textarea rows="6" value={form.description} onChange={(e)=>setForm({...form,description:e.target.value})}/></Field><div className="two-col"><Field label="Опыт работы, лет"><input type="number" min="0" value={form.experience} onChange={(e)=>setForm({...form,experience:e.target.value})}/></Field><Field label="Образование"><input value={form.education} onChange={(e)=>setForm({...form,education:e.target.value})}/></Field></div><div className="two-col"><Field label="Город"><select value={form.city_id} onChange={(e)=>setForm({...form,city_id:e.target.value,district_id:""})}><option value="">Не выбран</option>{cities.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></Field><Field label="Район"><select value={form.district_id} onChange={(e)=>setForm({...form,district_id:e.target.value})}><option value="">Не выбран</option>{districts.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></Field></div><Field label="Адрес приёма"><input value={form.address} onChange={(e)=>setForm({...form,address:e.target.value})}/></Field><button className="button button-dark">Сохранить изменения</button></form></div></>
}

function AdminPage() {
  const notify = useToast();
  const [tab, setTab] = useState("categories");
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);
  const [cities, setCities] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editor, setEditor] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState(() => new Set());
  const [expandedCities, setExpandedCities] = useState(() => new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [categoryItems, tagItems, cityItems] = await Promise.all([
        endpoints.adminCategories(),
        endpoints.adminTags(),
        endpoints.cities(),
      ]);
      const districtGroups = await Promise.all(
        cityItems.map(async (city) => {
          try {
            const items = await endpoints.districts(city.id);
            return items.map((district) => ({ ...district, city_name: city.name }));
          } catch {
            return [];
          }
        }),
      );
      setCategories(categoryItems);
      setTags(tagItems);
      setCities(cityItems);
      setDistricts(districtGroups.flat());
    } catch (error) {
      notify(safeError(error), "error");
    } finally {
      setLoading(false);
    }
  }, [notify]);

  useEffect(() => { load(); }, [load]);

  const lists = { categories, tags, cities };
  const navigation = [
    {
      title: "Каталог",
      description: "Структура и атрибуты каталога услуг",
      items: [
        { id: "categories", label: "Категории", icon: "grid" },
        { id: "tags", label: "Теги", icon: "settings" },
      ],
    },
    {
      title: "Локации",
      description: "Города и районы, доступные в сервисе",
      items: [
        { id: "cities", label: "Города и районы", icon: "pin" },
      ],
    },
  ];
  const sectionMeta = {
    categories: {
      eyebrow: "Каталог / Категории",
      title: "Категории услуг",
      text: "Управляйте иерархией направлений услуг. Корневые категории объединяют связанные подкатегории и используются для навигации по каталогу.",
      action: "Добавить категорию",
    },
    tags: {
      eyebrow: "Каталог / Теги",
      title: "Теги услуг",
      text: "Теги помогают уточнять особенности услуги и используются мастерами при оформлении предложений. Для одной услуги доступно до десяти тегов.",
      action: "Добавить тег",
    },
    cities: {
      eyebrow: "Локации / Города и районы",
      title: "Города и районы",
      text: "Управляйте географией сервиса: города выступают верхним уровнем, а районы создаются внутри соответствующего города.",
      action: "Добавить город",
    },
  };

  const toggleActive = async (type, item) => {
    try {
      if (type === "categories") await endpoints.updateCategory(item.id, { is_active: !item.is_active });
      if (type === "tags") await endpoints.updateTag(item.id, { is_active: !item.is_active });
      notify(item.is_active ? "Элемент скрыт из публичного интерфейса" : "Элемент снова доступен в публичном интерфейсе");
      await load();
    } catch (error) {
      notify(safeError(error), "error");
    }
  };

  const requestDelete = (kind, item) => {
    if (kind === "category") {
      const childrenCount = categories.filter((category) => category.parent_id === item.id).length;
      if (childrenCount) {
        notify(`Сначала удалите или перенесите подкатегории категории «${item.name}»`, "error");
        return;
      }
    }

    if (kind === "city") {
      const childrenCount = districts.filter((district) => district.city_id === item.id).length;
      if (childrenCount) {
        notify(`Сначала удалите районы города «${item.name}»`, "error");
        return;
      }
    }

    setDeleteTarget({ kind, item });
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    const { kind, item } = deleteTarget;
    setDeleting(true);

    try {
      if (kind === "category") await endpoints.deleteCategory(item.id);
      if (kind === "tag") await endpoints.deleteTag(item.id);
      if (kind === "city") await endpoints.deleteCity(item.id);
      if (kind === "district") await endpoints.deleteDistrict(item.id);

      notify({ category: `Категория «${item.name}» удалена`, tag: `Тег «${item.name}» удалён`, city: `Город «${item.name}» удалён`, district: `Район «${item.name}» удалён` }[kind]);
      setDeleteTarget(null);
      await load();
    } catch (error) {
      notify(safeError(error), "error");
    } finally {
      setDeleting(false);
    }
  };

  const meta = sectionMeta[tab];
  const items = lists[tab] || [];
  const rootCategoryItems = categories.filter((category) => !category.parent_id);
  const categoryChildren = (parentId) => categories.filter((category) => category.parent_id === parentId);
  const cityDistricts = (cityId) => districts.filter((district) => district.city_id === cityId);

  const toggleCategoryGroup = (categoryId) => {
    setExpandedCategories((current) => {
      const next = new Set(current);
      if (next.has(categoryId)) next.delete(categoryId);
      else next.add(categoryId);
      return next;
    });
  };

  const toggleCityGroup = (cityId) => {
    setExpandedCities((current) => {
      const next = new Set(current);
      if (next.has(cityId)) next.delete(cityId);
      else next.add(cityId);
      return next;
    });
  };

  const renderCategoryRow = (item, child = false) => (
    <div className={`admin-tree-row ${child ? "admin-tree-child" : "admin-tree-parent"}`} key={item.id}>
      {child ? (
        <div className="admin-tree-branch" aria-hidden="true">└</div>
      ) : (
        <button
          type="button"
          className="admin-tree-branch admin-tree-toggle"
          aria-label={expandedCategories.has(item.id) ? `Свернуть категорию ${item.name}` : `Развернуть категорию ${item.name}`}
          aria-expanded={expandedCategories.has(item.id)}
          title={expandedCategories.has(item.id) ? "Свернуть подкатегории" : "Показать подкатегории"}
          onClick={() => toggleCategoryGroup(item.id)}
        />
      )}
      <div className="admin-row-copy">
        <b>{item.name}</b>
        <span className="admin-tree-meta">
          <span>{child ? "Подкатегория" : "Основная категория"}</span>
          {!child && <span>{categoryChildren(item.id).length} подкатегорий</span>}
          <code>/{item.slug}</code>
        </span>
      </div>
      <div className="admin-row-controls">
        {typeof item.is_active === "boolean" && <span className={`status ${item.is_active ? "status-confirmed" : "status-cancelled"}`}>{item.is_active ? "Активно" : "Скрыто"}</span>}
        {!child && <button className="button button-ghost button-small admin-tree-add" onClick={() => setEditor({ type: "categories", item: null, parentId: item.id })}>Добавить подкатегорию</button>}
        <button className="button button-ghost button-small" onClick={() => toggleActive("categories", item)}>{item.is_active ? "Скрыть" : "Опубликовать"}</button>
        <button className="icon-button" title="Редактировать" onClick={() => setEditor({ type: "categories", item })}><Icon name="edit" size={17}/></button>
        <button className="icon-button danger" title="Удалить категорию" onClick={() => requestDelete("category", item)}><Icon name="trash" size={17}/></button>
      </div>
    </div>
  );

  const renderCategoryTree = () => (
    <div className="admin-table admin-tree-table">
      <div className="admin-table-caption admin-tree-caption">
        <div>
          <b>{meta.title}</b>
          <span>{rootCategoryItems.length} основных · {categories.length - rootCategoryItems.length} подкатегорий</span>
        </div>
        <div className="admin-tree-caption-actions">
          <button type="button" onClick={() => setExpandedCategories(new Set(rootCategoryItems.map((item) => item.id)))}>Развернуть все</button>
          <button type="button" onClick={() => setExpandedCategories(new Set())}>Свернуть все</button>
        </div>
      </div>
      {rootCategoryItems.map((parent) => (
        <div className={`admin-tree-group ${expandedCategories.has(parent.id) ? "is-expanded" : "is-collapsed"}`} key={parent.id}>
          {renderCategoryRow(parent)}
          {expandedCategories.has(parent.id) && categoryChildren(parent.id).map((child) => renderCategoryRow(child, true))}
        </div>
      ))}
    </div>
  );

  const renderCityTree = () => (
    <div className="admin-table admin-tree-table">
      <div className="admin-table-caption admin-tree-caption">
        <div>
          <b>{meta.title}</b>
          <span>{cities.length} городов · {districts.length} районов</span>
        </div>
        <div className="admin-tree-caption-actions">
          <button type="button" onClick={() => setExpandedCities(new Set(cities.map((city) => city.id)))}>Развернуть все</button>
          <button type="button" onClick={() => setExpandedCities(new Set())}>Свернуть все</button>
        </div>
      </div>
      {cities.map((city) => {
        const children = cityDistricts(city.id);
        return (
          <div className={`admin-tree-group ${expandedCities.has(city.id) ? "is-expanded" : "is-collapsed"}`} key={city.id}>
            <div className="admin-tree-row admin-tree-parent">
              <button
                type="button"
                className="admin-tree-branch admin-tree-toggle"
                aria-label={expandedCities.has(city.id) ? `Свернуть город ${city.name}` : `Развернуть город ${city.name}`}
                aria-expanded={expandedCities.has(city.id)}
                title={expandedCities.has(city.id) ? "Свернуть районы" : "Показать районы"}
                onClick={() => toggleCityGroup(city.id)}
              />
              <div className="admin-row-copy">
                <b>{city.name}</b>
                <span className="admin-tree-meta"><span>Город</span><span>{children.length} районов</span></span>
              </div>
              <div className="admin-row-controls">
                <button className="button button-ghost button-small admin-tree-add" onClick={() => setEditor({ type: "districts", item: null, cityId: city.id })}>Добавить район</button>
                <button className="icon-button" title="Редактировать город" onClick={() => setEditor({ type: "cities", item: city })}><Icon name="edit" size={17}/></button>
                <button className="icon-button danger" title="Удалить город" onClick={() => requestDelete("city", city)}><Icon name="trash" size={17}/></button>
              </div>
            </div>
            {expandedCities.has(city.id) && children.map((district) => (
              <div className="admin-tree-row admin-tree-child" key={district.id}>
                <div className="admin-tree-branch" aria-hidden="true">└</div>
                <div className="admin-row-copy">
                  <b>{district.name}</b>
                  <span className="admin-tree-meta"><span>Район</span><span>{city.name}</span></span>
                </div>
                <div className="admin-row-controls">
                  <button className="icon-button" title="Редактировать район" onClick={() => setEditor({ type: "districts", item: district, cityId: city.id })}><Icon name="edit" size={17}/></button>
                  <button className="icon-button danger" title="Удалить район" onClick={() => requestDelete("district", district)}><Icon name="trash" size={17}/></button>
                </div>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );

  const renderFlatTable = () => (
    <div className="admin-table">
      <div className="admin-table-caption">
        <b>{meta.title}</b>
        <span>Всего записей: {items.length}</span>
      </div>
      {items.map((item) => (
        <div className="admin-row" key={item.id}>
          <div className="admin-row-copy"><b>{item.name}</b><span>Slug: {item.slug}</span></div>
          <div className="admin-row-controls">
            {typeof item.is_active === "boolean" && <span className={`status ${item.is_active ? "status-confirmed" : "status-cancelled"}`}>{item.is_active ? "Активно" : "Скрыто"}</span>}
            <button className="button button-ghost button-small" onClick={() => toggleActive("tags", item)}>{item.is_active ? "Скрыть" : "Опубликовать"}</button>
            <button className="icon-button" title="Редактировать" onClick={() => setEditor({ type: tab, item })}><Icon name="edit" size={17}/></button>
            <button className="icon-button danger" title="Удалить тег" onClick={() => requestDelete("tag", item)}><Icon name="trash" size={17}/></button>
          </div>
        </div>
      ))}
    </div>
  );

  const hasItems = tab === "categories" ? categories.length > 0 : tab === "cities" ? cities.length > 0 : items.length > 0;

  return (
    <section className="section dashboard-section admin-page">
      <div className="container">
        <div className="admin-page-heading">
          <span className="eyebrow">Администрирование</span>
          <h1>Администрирование сервиса</h1>
          <p>Управляйте структурой каталога, тегами и географией сервиса. Связанные данные представлены в иерархическом виде для удобной навигации.</p>
        </div>

        <div className="admin-layout">
          <aside className="admin-sidebar">
            <div className="admin-sidebar-title">
              <Icon name="settings" size={18}/>
              <div><b>Справочники сервиса</b><span>Каталог и география</span></div>
            </div>
            {navigation.map((group) => (
              <div className="admin-nav-group" key={group.title}>
                <div className="admin-nav-group-copy"><b>{group.title}</b><span>{group.description}</span></div>
                <div className="admin-nav-list">
                  {group.items.map((item) => {
                    const count = item.id === "cities" ? cities.length + districts.length : lists[item.id].length;
                    return (
                      <button key={item.id} className={tab === item.id ? "active" : ""} onClick={() => setTab(item.id)}>
                        <Icon name={item.icon} size={17}/>
                        <span>{item.label}</span>
                        <small>{count}</small>
                        <Icon name="chevron" size={14}/>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </aside>

          <div className="admin-workspace">
            <DashboardHeader
              eyebrow={meta.eyebrow}
              title={meta.title}
              text={meta.text}
              action={meta.action}
              onAction={() => setEditor({ type: tab, item: null })}
            />

            <div className="admin-section-summary">
              {tab === "categories" && <>
                <div><span>Всего</span><b>{categories.length}</b></div>
                <div><span>Родительских</span><b>{rootCategoryItems.length}</b></div>
                <div><span>Подкатегорий</span><b>{categories.length - rootCategoryItems.length}</b></div>
                <div><span>Активных</span><b>{categories.filter((item) => item.is_active).length}</b></div>
              </>}
              {tab === "tags" && <>
                <div><span>Всего</span><b>{tags.length}</b></div>
                <div><span>Активных</span><b>{tags.filter((item) => item.is_active).length}</b></div>
                <div><span>Скрытых</span><b>{tags.filter((item) => !item.is_active).length}</b></div>
              </>}
              {tab === "cities" && <>
                <div><span>Городов</span><b>{cities.length}</b></div>
                <div><span>Районов</span><b>{districts.length}</b></div>
                <div><span>С районами</span><b>{cities.filter((city) => cityDistricts(city.id).length).length}</b></div>
              </>}
            </div>

            {loading ? <PanelLoader/> : hasItems ? (
              tab === "categories" ? renderCategoryTree() : tab === "cities" ? renderCityTree() : renderFlatTable()
            ) : (
              <div className="admin-empty">
                <div className="empty-icon"><Icon name="plus" size={26}/></div>
                <h3>В этом разделе пока нет данных</h3>
                <p>Добавьте первую запись, чтобы начать формировать справочник «{meta.title}».</p>
                <button className="button button-dark button-small" onClick={() => setEditor({ type: tab, item: null })}>{meta.action}</button>
              </div>
            )}
          </div>
        </div>
        {editor && <AdminEditor type={editor.type} item={editor.item} cities={cities} categories={categories} presetParentId={editor.parentId} presetCityId={editor.cityId} onClose={() => setEditor(null)} onSaved={async () => { setEditor(null); await load(); }}/>} 
        {deleteTarget && <DeleteConfirm target={deleteTarget} deleting={deleting} onClose={() => !deleting && setDeleteTarget(null)} onConfirm={confirmDelete}/>}
      </div>
    </section>
  );
}


function DeleteConfirm({ target, deleting, onClose, onConfirm }) {
  const labels = {
    category: { noun: "категорию", note: "Категория будет удалена из справочника без возможности восстановления." },
    tag: { noun: "тег", note: "Тег будет удалён из справочника без возможности восстановления." },
    city: { noun: "город", note: "Город будет удалён из справочника без возможности восстановления." },
    district: { noun: "район", note: "Район будет удалён из справочника без возможности восстановления." },
  };
  const copy = labels[target.kind];

  return (
    <Modal title="Подтверждение удаления" onClose={onClose}>
      <div className="delete-confirm">
        <div className="delete-confirm-icon"><Icon name="trash" size={24}/></div>
        <div>
          <h3>Удалить {copy.noun} «{target.item.name}»?</h3>
          <p>{copy.note} Если запись уже используется в услугах или профилях, сервер безопасно отменит удаление.</p>
        </div>
      </div>
      <div className="modal-actions">
        <button type="button" className="button button-ghost" onClick={onClose} disabled={deleting}>Отмена</button>
        <button type="button" className="button button-danger" onClick={onConfirm} disabled={deleting}>{deleting ? "Удаляем…" : "Удалить"}</button>
      </div>
    </Modal>
  );
}

function AdminEditor({ type, item, cities, categories, presetParentId = "", presetCityId = "", onClose, onSaved }) {
  const notify = useToast();
  const editing = Boolean(item);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: item?.name || "",
    slug: item?.slug || "",
    parent_id: item?.parent_id || presetParentId || "",
    city_id: item?.city_id || presetCityId || "",
  });

  const titles = {
    categories: editing ? "Редактировать категорию" : presetParentId ? "Добавление подкатегории" : "Добавление категории",
    tags: editing ? "Редактировать тег" : "Добавление тега",
    cities: editing ? "Редактировать город" : "Добавление города",
    districts: editing ? "Редактировать район" : "Добавление района",
  };

  const rootParentOptions = categories.filter((category) => !category.parent_id && category.id !== item?.id);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      if (type === "categories") {
        const data = { name: form.name, slug: form.slug, parent_id: form.parent_id || null };
        if (editing) await endpoints.updateCategory(item.id, data); else await endpoints.createCategory(data);
      } else if (type === "tags") {
        const data = { name: form.name, slug: form.slug };
        if (editing) await endpoints.updateTag(item.id, data); else await endpoints.createTag(data);
      } else if (type === "cities") {
        if (editing) await endpoints.updateCity(item.id, { name: form.name }); else await endpoints.createCity({ name: form.name });
      } else if (type === "districts") {
        if (editing) await endpoints.updateDistrict(item.id, { name: form.name });
        else await endpoints.createDistrict({ city_id: form.city_id, name: form.name });
      }
      notify(editing ? "Изменения сохранены" : "Новая запись создана");
      await onSaved();
    } catch (error) {
      notify(safeError(error), "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={titles[type]} onClose={onClose}>
      <form onSubmit={submit}>
        <Field label="Название"><input required minLength="2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}/></Field>
        {(type === "categories" || type === "tags") && <Field label="Slug" hint="Уникальный URL-идентификатор: латиница в нижнем регистре, слова разделяются дефисом"><input required minLength="2" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value.trim().toLowerCase().replace(/\s+/g, "-") })}/></Field>}
        {type === "categories" && <Field label="Родительская категория" hint="В качестве родителя доступны только категории верхнего уровня"><select value={form.parent_id} onChange={(e) => setForm({ ...form, parent_id: e.target.value })}><option value="">Без родителя — категория верхнего уровня</option>{rootParentOptions.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></Field>}
        {type === "districts" && <Field label="Город"><select required disabled={editing || Boolean(presetCityId)} value={form.city_id} onChange={(e) => setForm({ ...form, city_id: e.target.value })}><option value="">Выберите город</option>{cities.map((city) => <option key={city.id} value={city.id}>{city.name}</option>)}</select></Field>}
        <div className="modal-actions"><button type="button" className="button button-ghost" onClick={onClose}>Отмена</button><button disabled={saving} className="button button-dark">{saving ? "Сохраняем…" : editing ? "Сохранить изменения" : "Создать"}</button></div>
      </form>
    </Modal>
  );
}

function Field({ label, hint, children }) { return <label className="field"><span className="field-label">{label}</span>{children}{hint&&<small>{hint}</small>}</label>; }
function Pagination({page,totalPages,onPage}){if(totalPages<=1)return null;return <div className="pagination"><button disabled={page<=1} onClick={()=>onPage(page-1)}>←</button>{Array.from({length:Math.min(totalPages,5)},(_,i)=>{let p=i+1;if(totalPages>5&&page>3)p=page-2+i;if(p>totalPages)return null;return <button key={p} className={p===page?"active":""} onClick={()=>onPage(p)}>{p}</button>})}<button disabled={page>=totalPages} onClick={()=>onPage(page+1)}>→</button></div>}
function Modal({title,onClose,children,wide=false}){useEffect(()=>{const onKey=e=>e.key==="Escape"&&onClose();window.addEventListener("keydown",onKey);document.body.classList.add("modal-open");return()=>{window.removeEventListener("keydown",onKey);document.body.classList.remove("modal-open")}},[onClose]);return <div className="modal-backdrop" onMouseDown={(e)=>e.target===e.currentTarget&&onClose()}><div className={`modal ${wide?"modal-wide":""}`}><div className="modal-header"><h2>{title}</h2><button className="icon-button" onClick={onClose}><Icon name="close"/></button></div>{children}</div></div>}
function EmptyState({title,text,action,onAction}){return <div className="empty-state"><div className="empty-icon"><Icon name="calendar" size={32}/></div><h3>{title}</h3><p>{text}</p>{action&&<button className="button button-dark button-small" onClick={onAction}>{action}</button>}</div>}
function InlineError({text,retry}){return <div className="error-box"><b>Не удалось получить данные</b><p>{text}</p>{retry&&<button className="button button-ghost button-small" onClick={retry}>Повторить запрос</button>}</div>}
function PageLoader(){return <div className="page-loader"><span></span><b>MasterBooking</b></div>}
function PanelLoader(){return <div className="panel-loader"><span></span>Загружаем данные…</div>}
function AuthRequired(){return <section className="section"><div className="container"><EmptyState title="Требуется авторизация" text="Войдите в аккаунт, чтобы продолжить работу с этим разделом." action="Войти" onAction={()=>go("/auth")}/></div></section>}
function AccessDenied(){return <section className="section"><div className="container"><EmptyState title="Недостаточно прав" text="У вашей учётной записи нет доступа к этому разделу." action="Вернуться на главную" onAction={()=>go("/")}/></div></section>}
function NotFound(){return <section className="section"><div className="container"><EmptyState title="Страница не найдена" text="Проверьте адрес или вернитесь на главную страницу сервиса." action="Вернуться на главную" onAction={()=>go("/")}/></div></section>}
function Toast({toast,onClose}){return <div className={`toast toast-${toast.type}`}><span>{toast.type==="error"?"!":"✓"}</span><p>{toast.message}</p><button onClick={onClose}>×</button></div>}

createRoot(document.getElementById("root")).render(<React.StrictMode><App/></React.StrictMode>);
