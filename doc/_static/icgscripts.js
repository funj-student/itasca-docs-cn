/* Itasca 7.0 中文手册 — 共享导航脚本
 *
 * 移动端目录只有一个滚动容器：目录 iframe 自身的文档视口（浏览器原生滚动）。
 * 父级抽屉不再滚动，也不再使用 translateY / touchmove / preventDefault 模拟滚动。
 * 断点必须与 itasca.css 中的 @media (max-width: 959px) 保持一致。
 */
(function () {
  'use strict';

  var MOBILE_BREAKPOINT = 959;
  var MOBILE_QUERY = '(max-width: ' + MOBILE_BREAKPOINT + 'px)';
  var mobileMQ = window.matchMedia ? window.matchMedia(MOBILE_QUERY) : null;

  function isMobileNav() {
    return mobileMQ ? mobileMQ.matches : window.innerWidth <= MOBILE_BREAKPOINT;
  }

  function byId(id) { return document.getElementById(id); }

  var navOpen = false;
  var bodyLocked = false;
  var savedScrollY = 0;
  var suppressNavClick = false;
  var tocBoundFrame = null;
  var tocListenerInstalls = 0;

  /* ------------------------------------------------------------------ *
   * 目录抽屉的语义化外壳（由共用脚本注入，避免改动六千多篇 HTML）
   * ------------------------------------------------------------------ */
  function updateNavButton() {
    var btn = byId('navbutton');
    if (!btn) return;
    var label = btn.querySelector('.wb-nav-label');
    var aria = isMobileNav()
      ? (navOpen ? '关闭目录' : '打开目录')
      : (navOpen ? '收起目录' : '展开目录');
    btn.setAttribute('aria-label', aria);
    btn.setAttribute('aria-expanded', navOpen ? 'true' : 'false');
    if (label) label.textContent = isMobileNav() ? (navOpen ? '关闭' : '目录') : '目录';
  }

  function ensureNavUI() {
    var btn = byId('navbutton');
    var side = byId('mySidenav');

    if (btn && btn.getAttribute('role') !== 'button') {
      btn.setAttribute('role', 'button');
      btn.setAttribute('tabindex', '0');
      btn.setAttribute('aria-controls', 'mySidenav');
      btn.setAttribute('aria-expanded', 'false');
      btn.innerHTML = '<span class="wb-nav-icon" aria-hidden="true">☰</span><span class="wb-nav-label">目录</span>';
    }
    if (!byId('nav-backdrop')) {
      var backdrop = document.createElement('div');
      backdrop.id = 'nav-backdrop';
      backdrop.setAttribute('aria-hidden', 'true');
      document.body.appendChild(backdrop);
      backdrop.addEventListener('click', function () {
        if (navOpen && isMobileNav()) closeNav();
      });
    }
    if (side && !byId('nav-close')) {
      var closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.id = 'nav-close';
      closeBtn.setAttribute('aria-label', '关闭目录');
      closeBtn.innerHTML = '<span aria-hidden="true">✕</span><span>关闭</span>';
      closeBtn.addEventListener('click', function () { closeNav(); });
      side.insertBefore(closeBtn, side.firstChild);
    }
    updateNavButton();
    updateDrawerInert();
  }

  /* 目录关闭后，移动端抽屉内的元素不应仍可被 Tab 聚焦。
     inert 覆盖新版浏览器；tabindex/aria-hidden 作为旧浏览器兜底。 */
  function updateDrawerInert() {
    var side = byId('mySidenav');
    if (!side) return;
    var inert = isMobileNav() && !navOpen;
    if (inert !== side.inert) side.inert = inert;
    if (inert) side.setAttribute('aria-hidden', 'true');
    else side.removeAttribute('aria-hidden');
    Array.prototype.forEach.call(side.querySelectorAll('a, button, iframe'), function (el) {
      if (el.id === 'nav-close') return;
      if (inert) el.setAttribute('tabindex', '-1');
      else if (el.getAttribute('tabindex') === '-1') el.removeAttribute('tabindex');
    });
  }

  function focusInsideDrawer() {
    var side = byId('mySidenav');
    if (!side) return false;
    var active = document.activeElement;
    return !!active && (active === side || side.contains(active));
  }

  /* ------------------------------------------------------------------ *
   * 目录 iframe：只修正内部宽度与原生滚动，不接管滚动
   * ------------------------------------------------------------------ */
  function prepareTocFrame() {
    var frame = byId('toctobj2');
    if (!frame) return;
    function inject() {
      try {
        var d = frame.contentDocument || (frame.contentWindow && frame.contentWindow.document);
        if (!d || !d.head) return;
        if (!d.getElementById('wb-toc-native-scroll')) {
          var st = d.createElement('style');
          st.id = 'wb-toc-native-scroll';
          st.textContent = [
            'html{width:100%!important;overflow-x:hidden!important;margin:0!important;padding:0!important;-webkit-overflow-scrolling:touch;}',
            'body{width:100%!important;min-width:0!important;margin:0!important;padding-top:.5rem!important;overflow-x:hidden!important;-webkit-overflow-scrolling:touch;}',
            '#jstree,#jstree li,#jstree ul{width:auto!important;max-width:100%!important;}',
            '.jstree-anchor{white-space:normal!important;overflow-wrap:anywhere!important;}'
          ].join('');
          d.head.appendChild(st);
        }
        // 焦点进入 iframe 后，键盘事件不会冒泡到父页面；在同源 iframe 内补一个 Escape 监听。
        var root = d.documentElement || d.body;
        if (root && !root.getAttribute('data-wb-escape-ready')) {
          root.setAttribute('data-wb-escape-ready', '1');
          d.addEventListener('keydown', function (e) {
            if (e.key !== 'Escape' && e.key !== 'Esc') return;
            var parentNav = window.parent && window.parent.ItascaNav;
            if (parentNav && parentNav.isOpen && parentNav.isOpen()) {
              e.preventDefault();
              // 先让 iframe 内的焦点元素失焦，避免事件结束后浏览器把焦点又还给 iframe。
              if (d.activeElement && d.activeElement.blur) d.activeElement.blur();
              parentNav.closeFromIframe();
            }
          }, true);
        }
      } catch (e) { /* 跨域 iframe 不适用，保持原有行为 */ }
    }
    // 只在 iframe 元素首次出现或更换时安装一次 load 监听，避免重复注册。
    if (tocBoundFrame !== frame) {
      frame.addEventListener('load', inject);
      tocBoundFrame = frame;
      tocListenerInstalls++;
    }
    inject();
  }

  /* ------------------------------------------------------------------ *
   * 打开/关闭：移动端锁定背景滚动并保留阅读位置；桌面端保持侧栏行为
   * ------------------------------------------------------------------ */
  function lockPageScroll() {
    if (bodyLocked) return;
    savedScrollY = window.pageYOffset || document.documentElement.scrollTop || 0;
    document.body.style.position = 'fixed';
    document.body.style.top = (-savedScrollY) + 'px';
    document.body.style.left = '0';
    document.body.style.right = '0';
    document.body.style.width = '100%';
    bodyLocked = true;
  }

  function unlockPageScroll() {
    if (!bodyLocked) return;
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.left = '';
    document.body.style.right = '';
    document.body.style.width = '';
    bodyLocked = false;
    window.scrollTo(0, savedScrollY);
  }

  function openNav() {
    ensureNavUI();
    var side = byId('mySidenav');
    var main = byId('main');
    var btn = byId('navbutton');
    if (!side || !main) return;

    document.body.classList.add('nav-open');
    if (isMobileNav()) {
      lockPageScroll();
      side.style.width = '';
      side.style.height = '';
      main.style.marginLeft = '0';
      if (btn) btn.style.marginLeft = '0';
    } else {
      unlockPageScroll();
      side.style.width = '350px';
      main.style.marginLeft = '350px';
      if (btn) btn.style.marginLeft = '350px';
    }
    navOpen = true;
    updateNavButton();
    updateDrawerInert();
    prepareTocFrame();
    if (isMobileNav()) {
      var closeBtn = byId('nav-close');
      if (closeBtn) {
        try { closeBtn.focus({ preventScroll: true }); } catch (e) { closeBtn.focus(); }
      }
    }
  }

  function closeNav() {
    var side = byId('mySidenav');
    var main = byId('main');
    var btn = byId('navbutton');
    var restoreFocus = navOpen && isMobileNav() && focusInsideDrawer();

    document.body.classList.remove('nav-open');
    unlockPageScroll();
    if (side) { side.style.width = '0px'; side.style.height = ''; }
    if (main) main.style.marginLeft = '0px';
    if (btn) btn.style.marginLeft = '0px';
    navOpen = false;
    updateNavButton();
    updateDrawerInert();
    if (restoreFocus && btn) {
      function restore() {
        if (navOpen || !isMobileNav()) return;
        try { btn.focus({ preventScroll: true }); } catch (e) { btn.focus(); }
      }
      restore();
      // iframe 内的键盘事件结束后浏览器可能重新设置焦点，延时再恢复一次。
      setTimeout(restore, 0);
      setTimeout(restore, 60);
    }
  }

  function doNav() {
    if (navOpen) closeNav(); else openNav();
  }

  function toTop() {
    jQuery('html, body').animate({ scrollTop: 0 }, 'fast');
  }

  /* 只在布局模式真正切换时重置目录；地址栏/键盘导致的 resize 不关闭目录 */
  function applyLayoutMode() {
    closeNav();
    if (!isMobileNav()) openNav();
    prepareTocFrame();
  }

  function initNavEvents() {
    ensureNavUI();
    var btn = byId('navbutton');
    if (btn) {
      btn.addEventListener('click', function (e) {
        if (suppressNavClick) { suppressNavClick = false; e.preventDefault(); return; }
        doNav();
      });
      btn.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); doNav(); }
      });
      var startX = 0, startY = 0;
      btn.addEventListener('touchstart', function (e) {
        if (e.touches && e.touches.length) {
          startX = e.touches[0].clientX;
          startY = e.touches[0].clientY;
          suppressNavClick = false;
        }
      }, { passive: true });
      btn.addEventListener('touchmove', function (e) {
        if (e.touches && e.touches.length &&
            (Math.abs(e.touches[0].clientX - startX) > 10 || Math.abs(e.touches[0].clientY - startY) > 10)) {
          suppressNavClick = true;
        }
      }, { passive: true });
      btn.addEventListener('touchend', function () {
        setTimeout(function () { suppressNavClick = false; }, 350);
      }, { passive: true });
    }
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && navOpen && isMobileNav()) closeNav();
    });
  }

  initNavEvents();
  prepareTocFrame();

  if (mobileMQ) {
    if (mobileMQ.addEventListener) mobileMQ.addEventListener('change', applyLayoutMode);
    else if (mobileMQ.addListener) mobileMQ.addListener(applyLayoutMode);
  }

  function applyInitialLayout() {
    if (isMobileNav()) {
      closeNav();
    } else {
      openNav();
      var btn = byId('navbutton');
      if (btn && window.jQuery) jQuery(btn).css({ opacity: 0 }).animate({ opacity: 1 }, 2800);
    }
  }
  if (document.readyState === 'complete') applyInitialLayout();
  else window.addEventListener('load', applyInitialLayout);

  /* ------------------------------------------------------------------ *
   * 以下为原有页面增强逻辑，未做技术内容改动
   * ------------------------------------------------------------------ */

  // 目录链接指向当前章节
  var toc = byId('toctobj2');
  if (toc) {
    var href = window.location.href;
    if (href.lastIndexOf('flac3d/') > 1) { href = href.substring(href.lastIndexOf('flac3d/')); }
    if (href.lastIndexOf('common/') > 1) { href = href.substring(href.lastIndexOf('common/')); }
    if (href.lastIndexOf('pfc/') > 1) { href = href.substring(href.lastIndexOf('pfc/')); }
    if (href.lastIndexOf('udec/') > 1) { href = href.substring(href.lastIndexOf('udec/')); }
    if (href.lastIndexOf('3dec/') > 1) { href = href.substring(href.lastIndexOf('3dec/')); }
    toc.src = toc.src + '?' + href;
  }

  // 动态切换 logo / 名称，并设置代码页的返回首页链接
  var f = byId('cornerlogo');
  var t = window.location.href;
  if (f) {
    if (t.lastIndexOf('/html/flac3d/') > 0 || t.lastIndexOf('/doc/flac3d/') > 0 || t.lastIndexOf('/flac3d/docproject/') > 0) {
      f.src = f.src.substring(0, f.src.lastIndexOf('/')) + '/flac3d32.png';
      byId('cornercodename').innerHTML = 'FLAC3D';
      byId('cornerlink').href = t.substring(0, t.lastIndexOf('/flac3d/')) + '/flac3d/docproject/source/flac3dhome.html';
    }
    if (t.lastIndexOf('/html/pfc/') > 0 || t.lastIndexOf('/doc/pfc/') > 0) {
      f.src = f.src.substring(0, f.src.lastIndexOf('/')) + '/pfc3d32.png';
      byId('cornercodename').innerHTML = 'PFC';
      byId('cornerlink').href = t.substring(0, t.lastIndexOf('/pfc/')) + '/pfc/docproject/source/manual/pfchome.html';
    }
    if (t.lastIndexOf('/html/3dec/') > 0 || t.lastIndexOf('/doc/3dec/') > 0) {
      f.src = f.src.substring(0, f.src.lastIndexOf('/')) + '/3dec32.png';
      byId('cornercodename').innerHTML = '3DEC';
      byId('cornerlink').href = t.substring(0, t.lastIndexOf('/3dec/')) + '/3dec/docproject/source/3dechome.html';
    }
  }

  // 按产品显示对应的内容块
  if (jQuery('#pagecodeid').length > 0) {
    var codeis;
    if (jQuery('#pagecodeid').html() === 'common') {
      codeis = jQuery('#codeid')[0].innerHTML;
    } else {
      codeis = jQuery('#pagecodeid').html();
    }
    jQuery('span.codeis').text(codeis);
    var codeclass = codeis !== '3DEC' ? '.' + codeis.toLowerCase() : '.dec';
    jQuery('div' + codeclass).css('display', 'block');
    jQuery('span' + codeclass).css('display', 'inline');
  }

  // 双击标题/表格显示元素 id（仅本地调试环境）
  jQuery('h1,h2,h3,h4,.h1,.h2,.h3,.h4,table,p').dblclick(function () {
    if (window.location.href.indexOf('/wad700/') === -1) return;
    var head_tag = document.getElementsByTagName('head')[0];
    if (head_tag.innerHTML.indexOf('jquery-ui.js') === -1) {
      jQuery(this).prop('title', 'That was the first double-click');
      var script_tag = document.createElement('script');
      script_tag.setAttribute('src', 'https://code.jquery.com/ui/1.12.1/jquery-ui.js');
      head_tag.appendChild(script_tag);
      var link_tag = document.createElement('link');
      link_tag.setAttribute('rel', 'stylesheet');
      link_tag.setAttribute('href', 'https://code.jquery.com/ui/1.12.1/themes/smoothness/jquery-ui.css');
      head_tag.appendChild(link_tag);
      jQuery("<style type='text/css'> .superlocal{ font-size:1em; font-family: unset;} </style>").appendTo('head');
      return;
    }
    jQuery(this).prop('title', ' ');
    var par = this.parentElement ? [this.parentElement.tagName, this.parentElement.id] : ['none', '(n/a)'];
    var pre = this.previousElementSibling ? [this.previousElementSibling.tagName, this.previousElementSibling.id] : ['none', '(n/a)'];
    var nex = this.nextElementSibling ? [this.nextElementSibling.tagName, this.nextElementSibling.id] : ['none', '(n/a)'];
    var chi = this.firstElementChild ? [this.firstElementChild.tagName, this.firstElementChild.id] : ['none', '(n/a)'];
    var msg = '\xa0\u2196\xa0\xa0' + par[0] + ': ' + par[1] + '<br>' +
              '\xa0\u2191\xa0\xa0' + pre[0] + ': ' + pre[1] + '<br>' +
              '\u2192 ' + this.tagName + ': ' + this.id + '<br>' +
              '\xa0\u2193\xa0\xa0' + nex[0] + ': ' + nex[1] + '<br>' +
              '\xa0\u2198\xa0\xa0' + chi[0] + ': ' + chi[1];
    jQuery('<div>' + msg + '</div>').dialog({
      title: 'Local IDs', width: 400, dialogClass: 'superlocal'
    });
  });

  /* ------------------------------------------------------------------ *
   * 正文适配：为技术表格提供独立的横向滚动容器和提示；
   * 仅对确实过长、不可断行的单个标记启用局部滚动。
   * ------------------------------------------------------------------ */
  function enhanceContentTables() {
    /* Doxygen API 页使用 div.contents 而非 #mainbody；两类正文都需要表格滚动容器。 */
    var main = byId('mainbody') || document.querySelector('div.contents');
    if (!main) return;
    /* 脚注表、blank 布局表也可能包含长技术名称，必须同样获得局部滚动容器。 */
    var tables = main.querySelectorAll('table');
    Array.prototype.forEach.call(tables, function (table) {
      if (table.parentElement && table.parentElement.classList.contains('table-scroll')) return;
      var wrap = document.createElement('div');
      wrap.className = 'table-scroll';
      wrap.tabIndex = 0;
      wrap.setAttribute('role', 'region');
      wrap.setAttribute('aria-label', '表格区域，可左右滑动查看完整内容');
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(table);
    });
    // 布局稳定后再判断是否需要滑动提示
    requestAnimationFrame(function () {
      Array.prototype.forEach.call(main.querySelectorAll('.table-scroll'), function (wrap) {
        if (wrap.querySelector('.table-scroll-hint')) return;
        if (wrap.scrollWidth > wrap.clientWidth + 2) {
          var hint = document.createElement('span');
          hint.className = 'table-scroll-hint';
          hint.textContent = '← 左右滑动查看完整表格 →';
          wrap.insertAdjacentElement('afterend', hint);
        }
      });
    });
  }

  function enhanceLongTokens() {
    var main = byId('mainbody');
    if (!main) return;
    var selector = 'code, span.pre, span.cmdname, span.cmdopt, span.cmdkey, span.fishname, span.fishcmd, span.varstring, a';
    Array.prototype.forEach.call(main.querySelectorAll(selector), function (el) {
      if (el.dataset.wbTokenChecked || el.children.length) return;
      el.dataset.wbTokenChecked = '1';
      var text = (el.textContent || '').trim();
      if (!text || /\s/.test(text) || text.length < 24) return;
      var r = el.getBoundingClientRect();
      var parent = el.parentElement;
      if (!parent || r.width <= parent.getBoundingClientRect().width - 4) return;
      el.classList.add('wb-long-token');
    });
  }

  function initContentEnhancements() {
    enhanceContentTables();
    enhanceLongTokens();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initContentEnhancements);
  } else {
    initContentEnhancements();
  }

  // 公开少量状态，便于自动化测试与后续维护
  window.ItascaNav = {
    isMobile: isMobileNav,
    open: openNav,
    close: closeNav,
    closeFromIframe: closeNav,
    toggle: doNav,
    isOpen: function () { return navOpen; },
    // 供回归测试确认 load 监听器只安装一次
    tocListenerInstalls: function () { return tocListenerInstalls; },
    isDrawerInert: function () {
      var side = byId('mySidenav');
      return !!side && !!side.inert;
    }
  };
})();
