# WEB_ALL

Сайт-портал по двум курсам: **3 курс** («Средства создания приложений») и **4 курс** (JS · PHP · Node).

Стек: HTML, CSS, JavaScript. Без сборщиков, фреймворков и автогенерации.

**Онлайн:** https://sleptsov-sca.netlify.app/

---

## Навигация по сайту

```
index.html              выбор курса (3 или 4)
    ├── portal.html     3 курс: карточки разделов
    │       ↓
    │   pages/lab.html  каталог (лабораторные, лекции, контроль, практика)
    └── course-4.html   4 курс: Лекции, ЛР, ОКР
```

Работы и описания открываются **в панели справа** — без iframe, через `fetch` и вставку HTML.

---

## Структура папки WEB_ALL

```
WEB_ALL/
│
├── index.html              вход: выбор 3 / 4 курса
├── portal.html             главная 3 курса
├── course-4.html           главная 4 курса
├── README.md               эта документация
│
├── assets/images/          логотипы и иконки портала
├── css/                    стили (точка входа — main.css)
├── js/                     меню и просмотрщик материалов
├── pages/                  страницы разделов и overviews/
├── materials/              файлы курса для сайта
└── all files/              архив исходников (не на Netlify)
```

### assets/images/

Логотипы портала, GitHub, Voxiva. Картинки из лабораторных лежат в `materials/`, не здесь.

### css/

```
css/
├── main.css                      сборка всех стилей
├── base/                         переменные, сброс
├── layout/                       сетка, шапка, меню, подвал
├── components/
│   ├── portal-home.css           главная portal.html
│   ├── ad-panel.css              блок рекламы
│   └── catalog/                  каталог + просмотрщик
│       ├── layout.css            список | панель
│       ├── groups.css            аккордеон лабораторных
│       ├── day-overview.css      описание занятия
│       ├── viewer.css            панель просмотра
│       └── responsive.css        мобильная вёрстка
├── pages/                        splash, страница обзора
└── media/responsive.css          адаптив меню и шапки
```

Где править оформление:

- цвета → `css/base/variables.css`
- кнопки в списке → `css/components/catalog/groups.css`
- панель просмотра → `css/components/catalog/viewer.css`
- текст описания → `day-overview.css`, `day-overview-page.css`

### js/

```
js/
├── nav/mobile-nav.js                 бургер-меню
└── viewer/
    ├── material-viewer-scope.js      изоляция CSS работ
    └── material-viewer.js            загрузка в панель (без iframe)
```

Просмотрщик ищет ссылки с `data-material-src`, подгружает HTML в `#material-content`, чинит пути к картинкам и скриптам. Описания из `pages/overviews/` показываются в панели — только блок с текстом, без шапки сайта.

На телефоне вверху панели — кнопка «↑ Лабораторная …» для возврата к раскрытой работе в списке.

После правок JS увеличьте версию в подключении (`?v=17` и далее).

### pages/

```
pages/
├── lab.html                14 лабораторных (3 курс)
├── lection.html            8 лекций
├── control.html            ОКР 1
├── practice.html           Flex и Grid
├── web-practice.html       ссылка на WEB-практику
├── about.html              обо мне
├── course-4/               4 курс: Лекции, ЛР, ОКР
└── overviews/
    ├── lab-01 … lab-14
    ├── lection-01 … lection-08
    ├── practice-01
    └── control-okr1
```

Каталог: слева аккордеон, справа просмотр. В раскрытой лабораторной три блока:

1. **Условие** — PDF  
2. **Описание** — страница занятия  
3. **Выполненное задание** — HTML-работы  

В `overviews/` — название («Лаб 1»), темы, «Что я сделал», ссылки. Без дат. Текст правится вручную в HTML.

### materials/

Копии для сайта. Исходники 3 курса: `COURSE_3/LAB/`, `COURSE_3/LECTION/`, `COURSE_3/CONTROL/`, `COURSE_3/PRACTICE/`. Исходники 4 курса: `COURSE_4/JS_PHP_NODE/`.

```
materials/
├── lab/NN/           Условие/, Примеры/, иногда Индивидуальное/
├── lection/NN/       Материалы/, примеры HTML
├── control/OKR-1/    контрольные работы
└── practice/01/      условия и примеры Flex/Grid
```

При переносе файлов обновите ссылки в `pages/lab.html` и `pages/overviews/`.

### all files/

Архив материалов в старой структуре папок. На сайт не публикуется.

---

## Редактирование каталога

Каждая лабораторная — `<details class="lab-group">` в `pages/lab.html`.

Для открытия в панели у ссылки нужен `data-material-src`. Классы:

- `lab-files__link--pdf` — PDF в новой вкладке  
- `lab-files__link--html` — работа в панели  
- `lab-files__link--overview` — описание в панели  

Путь к обзору: `overviews/lab-NN.html` (от папки `pages/`).

### Новая лабораторная

1. Файлы → `materials/lab/NN/`  
2. Блок в `pages/lab.html`  
3. Страница `pages/overviews/lab-NN.html`  
4. При необходимости — исходники в `COURSE_3/LAB/`  

---

## Локальный запуск

Нужен веб-сервер (`fetch` не работает через `file://`).

```bash
cd WEB_ALL
npx --yes serve .
```

Или Live Server на папку `WEB_ALL` → `http://localhost:3000/`

---

## Репозиторий

```
Pavel-Sleptsov/
├── COURSE_3/         материалы 3 курса (LAB, LECTION, CONTROL, PRACTICE, WEB_PRACTICE)
├── COURSE_4/         JS_PHP_NODE (LECTION, LAB, OKR)
└── WEB_ALL/          этот портал → Netlify
```

**Публикация:** корень Netlify — `WEB_ALL`. После push: https://sleptsov-sca.netlify.app/

---

## Автор

Слепцов Павел Леонидович · Минский филиал БТЭУ ПК  
https://github.com/PavelCRG
