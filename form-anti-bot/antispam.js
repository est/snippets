/**
 * FormGuard — Behavior-based anti-spam library
 *
 * Detects bot submissions by analyzing typing patterns, paste events,
 * mouse/touch activity, programmatic value assignment, and honeypots.
 *
 * Usage:
 *   const guard = new FormGuard(document.querySelector('form'), {
 *     threshold: 60,
 *     onBlock: (report) => console.warn('Spam detected', report),
 *   });
 *   guard.onSubmit((report, allow) => {
 *     if (report.isSpam) { /* show error *\/ } else { allow(); }
 *   });
 */

(function (global) {
  'use strict';

  // ─── Utilities ────────────────────────────────────────────────────────────

  function generateToken() {
    const arr = new Uint8Array(18);
    crypto.getRandomValues(arr);
    return btoa(String.fromCharCode(...arr)).replace(/[+/=]/g, (c) =>
      ({ '+': '-', '/': '_', '=': '' }[c])
    );
  }

  function stddev(values) {
    if (values.length < 2) return Infinity;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance =
      values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length;
    return Math.sqrt(variance);
  }

  function clamp(val, min, max) {
    return Math.min(Math.max(val, min), max);
  }

  // ─── FormGuard ─────────────────────────────────────────────────────────────

  class FormGuard {
    /**
     * @param {HTMLFormElement} formElement
     * @param {object} [options]
     * @param {number}  [options.threshold=60]       Risk score (0-100) at which submit is blocked
     * @param {boolean} [options.injectHoneypot=true] Auto-inject a hidden honeypot field
     * @param {boolean} [options.injectToken=true]   Auto-inject a JS-session token
     * @param {function} [options.onChange]          Called on every score change: (score, signals) => void
     * @param {function} [options.onBlock]           Called when spam is detected: (report) => void
     */
    constructor(formElement, options = {}) {
      if (!(formElement instanceof HTMLFormElement)) {
        throw new TypeError('FormGuard: first argument must be an HTMLFormElement');
      }

      this.form = formElement;
      this.threshold = options.threshold ?? 60;
      this.injectHoneypot = options.injectHoneypot !== false;
      this.injectToken = options.injectToken !== false;
      this._onChange = options.onChange || null;
      this._onBlock = options.onBlock || null;
      this._submitCallback = null;

      // ── Telemetry state ──────────────────────────────────────────────────
      this.pageLoadTime = Date.now();
      this.firstInteractionTime = null;

      // Per-field maps keyed by field name or generated id
      this._inputEvents = new Map();    // fieldKey → count of genuine input events
      this._keyIntervals = new Map();   // fieldKey → [ms intervals between keydowns]
      this._lastKeyTime = new Map();    // fieldKey → timestamp of last keydown
      this._focusedFields = new Set();  // fieldKeys that received focus
      this._pastedFields = new Map();   // fieldKey → { count, chars }
      this._programmaticFields = new Set(); // fieldKeys where .value= was detected

      this.mouseMovements = 0;
      this.touchEvents = 0;
      this._honeypotFilled = false;
      this._token = null;
      this._honeypotFieldName = null;
      this._tokenFieldName = null;

      this._boundHandlers = {};

      this._setup();
    }

    // ─── Setup ──────────────────────────────────────────────────────────────

    _setup() {
      if (this.injectHoneypot) this._injectHoneypot();
      if (this.injectToken) this._injectToken();
      this._interceptValueSetters();
      this._bindFormEvents();
      this._bindGlobalEvents();
    }

    _injectHoneypot() {
      const name = '_fgp_' + generateToken().slice(0, 8);
      this._honeypotFieldName = name;

      const wrapper = document.createElement('div');
      // Hidden from humans, visible to bots that parse DOM without CSS
      wrapper.setAttribute('aria-hidden', 'true');
      Object.assign(wrapper.style, {
        opacity: '0',
        position: 'absolute',
        top: '-9999px',
        left: '-9999px',
        height: '0',
        width: '0',
        overflow: 'hidden',
        pointerEvents: 'none',
        tabIndex: '-1',
      });

      const label = document.createElement('label');
      label.textContent = 'Leave this field empty';
      label.htmlFor = name;

      const input = document.createElement('input');
      input.type = 'text';
      input.name = name;
      input.id = name;
      input.autocomplete = 'off';
      input.tabIndex = -1;

      input.addEventListener('input', () => {
        if (input.value.length > 0) {
          this._honeypotFilled = true;
          this._notifyChange();
        }
      });

      wrapper.appendChild(label);
      wrapper.appendChild(input);
      this.form.appendChild(wrapper);
    }

    _injectToken() {
      const name = '_fgt_' + generateToken().slice(0, 8);
      this._tokenFieldName = name;
      this._token = generateToken();

      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = name;
      input.value = this._token;
      this.form.appendChild(input);
    }

    /**
     * Intercepts HTMLInputElement.value setter for all current form fields
     * to detect programmatic assignment (e.g. field.value = "text").
     * This fires *before* any input event would fire, so we can distinguish
     * from genuine user typing.
     */
    _interceptValueSetters() {
      const self = this;
      const proto = HTMLInputElement.prototype;
      const textAreaProto = HTMLTextAreaElement.prototype;

      function patchProto(p) {
        if (p._fgPatched) return;

        const descriptor = Object.getOwnPropertyDescriptor(p, 'value');
        if (!descriptor || !descriptor.set) return;

        const originalSet = descriptor.set;
        const originalGet = descriptor.get;

        Object.defineProperty(p, 'value', {
          get: originalGet,
          set(newValue) {
            const el = this;
            originalSet.call(el, newValue);

            // Only flag fields that belong to a FormGuard-watched form
            if (el.form === self.form && el.name !== self._honeypotFieldName && el.name !== self._tokenFieldName) {
              if (newValue && newValue.toString().length > 0) {
                const key = self._fieldKey(el);
                // If setter fires but no input events yet recorded, mark as programmatic.
                // Use a microtask so any synchronously-dispatched input event fires first.
                Promise.resolve().then(() => {
                  const currentInputCount = self._inputEvents.get(key) || 0;
                  if (currentInputCount === 0 && el.value.length > 0) {
                    self._programmaticFields.add(key);
                    self._notifyChange();
                  }
                });
              }
            }
          },
          configurable: true,
        });

        p._fgPatched = true;
      }

      patchProto(proto);
      patchProto(textAreaProto);
    }

    _bindFormEvents() {
      const form = this.form;

      const fields = () =>
        Array.from(form.elements).filter(
          (el) =>
            (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') &&
            el.name !== this._honeypotFieldName &&
            el.name !== this._tokenFieldName &&
            el.type !== 'hidden' &&
            el.type !== 'submit' &&
            el.type !== 'button'
        );

      const onKeydown = (e) => {
        const key = this._fieldKey(e.target);
        const now = Date.now();
        if (this.firstInteractionTime === null) this.firstInteractionTime = now;

        const last = this._lastKeyTime.get(key);
        if (last !== undefined) {
          const interval = now - last;
          if (!this._keyIntervals.has(key)) this._keyIntervals.set(key, []);
          this._keyIntervals.get(key).push(interval);
        }
        this._lastKeyTime.set(key, now);
        this._notifyChange();
      };

      const onInput = (e) => {
        const key = this._fieldKey(e.target);
        this._inputEvents.set(key, (this._inputEvents.get(key) || 0) + 1);
        // If there's an input event, field is NOT purely programmatic
        this._programmaticFields.delete(key);
        this._notifyChange();
      };

      const onFocus = (e) => {
        this._focusedFields.add(this._fieldKey(e.target));
        this._notifyChange();
      };

      const onPaste = (e) => {
        const key = this._fieldKey(e.target);
        if (this.firstInteractionTime === null) this.firstInteractionTime = Date.now();

        const cd = e.clipboardData || window.clipboardData;
        const pastedText = cd ? cd.getData('text') : '';
        const existing = this._pastedFields.get(key) || { count: 0, chars: 0 };
        this._pastedFields.set(key, {
          count: existing.count + 1,
          chars: existing.chars + pastedText.length,
        });
        this._notifyChange();
      };

      const onSubmit = (e) => {
        e.preventDefault();
        const report = this.generateReport();
        if (this._submitCallback) {
          this._submitCallback(report, () => this.form.submit());
        } else if (report.isSpam) {
          if (this._onBlock) this._onBlock(report);
        } else {
          this.form.submit();
        }
      };

      this._boundHandlers = { onKeydown, onInput, onFocus, onPaste, onSubmit };

      // Delegate on form for all fields
      form.addEventListener('keydown', onKeydown, true);
      form.addEventListener('input', onInput, true);
      form.addEventListener('focus', onFocus, true);
      form.addEventListener('paste', onPaste, true);
      form.addEventListener('submit', onSubmit);
    }

    _bindGlobalEvents() {
      const onMouseMove = () => {
        this.mouseMovements++;
        if (this.mouseMovements > 5) {
          // Unbind after enough data — no need to keep counting
          document.removeEventListener('mousemove', onMouseMove);
        }
        this._notifyChange();
      };

      const onTouch = () => {
        this.touchEvents++;
        this._notifyChange();
      };

      document.addEventListener('mousemove', onMouseMove, { passive: true });
      document.addEventListener('touchstart', onTouch, { passive: true });
      document.addEventListener('touchmove', onTouch, { passive: true });
    }

    // ─── Core Scoring ────────────────────────────────────────────────────────

    /**
     * Computes a risk score from 0 (clean) to 100 (definitely spam).
     * Returns { score, signals } where signals is a breakdown of each check.
     */
    calculateRiskScore() {
      const signals = [];
      let score = 0;

      // 1. Honeypot filled
      if (this._honeypotFilled) {
        signals.push({ id: 'honeypot', label: '蜜罐字段被填写', risk: 40, triggered: true });
        score += 40;
      } else {
        signals.push({ id: 'honeypot', label: '蜜罐字段被填写', risk: 40, triggered: false });
      }

      // 2. Page time too short (< 3s)
      const elapsed = Date.now() - this.pageLoadTime;
      if (elapsed < 3000) {
        const penalty = Math.round(25 * (1 - elapsed / 3000));
        signals.push({ id: 'page_time', label: `页面停留时间过短 (${(elapsed / 1000).toFixed(1)}s)`, risk: 25, triggered: true, penalty });
        score += penalty;
      } else {
        signals.push({ id: 'page_time', label: `页面停留时间 (${(elapsed / 1000).toFixed(1)}s)`, risk: 25, triggered: false, penalty: 0 });
      }

      // 3. Fields with value but zero genuine input events (programmatic assignment)
      const programmaticCount = this._programmaticFields.size;
      if (programmaticCount > 0) {
        signals.push({ id: 'programmatic', label: `检测到程序赋值字段 (${programmaticCount} 个)`, risk: 30, triggered: true });
        score += 30;
      } else {
        signals.push({ id: 'programmatic', label: '无程序赋值字段', risk: 30, triggered: false });
      }

      // 4. Keystroke interval stddev too small (robotic uniform speed)
      let minStddev = Infinity;
      let fastFieldKey = null;
      for (const [key, intervals] of this._keyIntervals) {
        if (intervals.length >= 4) {
          const sd = stddev(intervals);
          if (sd < minStddev) {
            minStddev = sd;
            fastFieldKey = key;
          }
        }
      }

      if (fastFieldKey !== null && minStddev < 15) {
        signals.push({ id: 'keystroke_stddev', label: `击键节奏过于均匀 (stddev=${minStddev.toFixed(1)}ms)`, risk: 25, triggered: true });
        score += 25;
      } else if (fastFieldKey !== null) {
        signals.push({ id: 'keystroke_stddev', label: `击键节奏正常 (stddev=${minStddev.toFixed(1)}ms)`, risk: 25, triggered: false });
      } else {
        signals.push({ id: 'keystroke_stddev', label: '击键节奏 (数据不足)', risk: 25, triggered: false });
      }

      // 5. Average keystroke interval < 30ms (superhuman speed)
      let superhumanTriggered = false;
      for (const [, intervals] of this._keyIntervals) {
        if (intervals.length >= 4) {
          const avg = intervals.reduce((a, b) => a + b, 0) / intervals.length;
          if (avg < 30) {
            superhumanTriggered = true;
            break;
          }
        }
      }
      if (superhumanTriggered) {
        signals.push({ id: 'superhuman_speed', label: '击键速度超人 (avg < 30ms)', risk: 20, triggered: true });
        score += 20;
      } else {
        signals.push({ id: 'superhuman_speed', label: '击键速度正常', risk: 20, triggered: false });
      }

      // 6. Paste events detected (strict mode: any paste is suspicious)
      let totalPastedChars = 0;
      let totalInputEventChars = 0;
      for (const [key, data] of this._pastedFields) {
        totalPastedChars += data.chars;
      }
      for (const [key] of this._inputEvents) {
        const el = this.form.elements.namedItem(key);
        if (el) totalInputEventChars += (el.value || '').length;
      }

      if (totalPastedChars > 0) {
        signals.push({ id: 'paste', label: `检测到粘贴事件 (${totalPastedChars} 字符)`, risk: 15, triggered: true });
        score += 15;

        // Extra penalty: pasted chars > 80% of total field content
        const totalFieldChars = this._getTotalFieldChars();
        if (totalFieldChars > 0 && totalPastedChars / totalFieldChars > 0.8) {
          signals.push({ id: 'paste_ratio', label: `粘贴内容占比过高 (${Math.round(totalPastedChars / totalFieldChars * 100)}%)`, risk: 10, triggered: true });
          score += 10;
        } else {
          signals.push({ id: 'paste_ratio', label: '粘贴内容占比正常', risk: 10, triggered: false });
        }
      } else {
        signals.push({ id: 'paste', label: '无粘贴事件', risk: 15, triggered: false });
        signals.push({ id: 'paste_ratio', label: '粘贴内容占比正常', risk: 10, triggered: false });
      }

      // 7. No mouse or touch events
      const hasPointerActivity = this.mouseMovements > 0 || this.touchEvents > 0;
      if (!hasPointerActivity) {
        signals.push({ id: 'no_pointer', label: '无鼠标/触摸移动事件', risk: 10, triggered: true });
        score += 10;
      } else {
        signals.push({ id: 'no_pointer', label: `检测到指针活动 (mouse=${this.mouseMovements}, touch=${this.touchEvents})`, risk: 10, triggered: false });
      }

      // 8. Fields with value but no focus event (never focused = programmatic fill)
      const unfocusedFilledCount = this._countUnfocusedFilledFields();
      if (unfocusedFilledCount > 0) {
        signals.push({ id: 'no_focus', label: `字段有值但未获得焦点 (${unfocusedFilledCount} 个)`, risk: 20, triggered: true });
        score += 20;
      } else {
        signals.push({ id: 'no_focus', label: '所有非空字段均获得了焦点', risk: 20, triggered: false });
      }

      score = clamp(score, 0, 100);
      return { score, signals };
    }

    _getTotalFieldChars() {
      let total = 0;
      for (const el of this.form.elements) {
        if (
          (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') &&
          el.name !== this._honeypotFieldName &&
          el.name !== this._tokenFieldName &&
          el.type !== 'hidden' &&
          el.type !== 'submit' &&
          el.type !== 'button'
        ) {
          total += (el.value || '').length;
        }
      }
      return total;
    }

    _countUnfocusedFilledFields() {
      let count = 0;
      for (const el of this.form.elements) {
        if (
          (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') &&
          el.name !== this._honeypotFieldName &&
          el.name !== this._tokenFieldName &&
          el.type !== 'hidden' &&
          el.type !== 'submit' &&
          el.type !== 'button' &&
          (el.value || '').length > 0
        ) {
          const key = this._fieldKey(el);
          if (!this._focusedFields.has(key)) {
            count++;
          }
        }
      }
      return count;
    }

    /**
     * Generates a full human-readable + machine-parseable report.
     * Safe to send to a backend for secondary validation.
     */
    generateReport() {
      const { score, signals } = this.calculateRiskScore();
      const isSpam = score >= this.threshold;

      return {
        isSpam,
        score,
        threshold: this.threshold,
        verdict: isSpam ? 'SPAM' : 'CLEAN',
        token: this._token,
        timing: {
          pageLoadTime: this.pageLoadTime,
          firstInteraction: this.firstInteractionTime,
          elapsedMs: Date.now() - this.pageLoadTime,
        },
        signals,
        raw: {
          mouseMovements: this.mouseMovements,
          touchEvents: this.touchEvents,
          honeypotFilled: this._honeypotFilled,
          programmaticFields: Array.from(this._programmaticFields),
          focusedFields: Array.from(this._focusedFields),
          pastedFields: Object.fromEntries(this._pastedFields),
          keystrokeIntervals: Object.fromEntries(this._keyIntervals),
        },
      };
    }

    /**
     * Register a callback that fires on form submit.
     * Callback receives (report, allow) where allow() programmatically submits the form.
     *
     * @param {function} callback  (report: ReportObject, allow: () => void) => void
     */
    onSubmit(callback) {
      this._submitCallback = callback;
    }

    /**
     * Returns current score without triggering submit logic.
     * Useful for real-time UI updates.
     */
    getCurrentScore() {
      return this.calculateRiskScore();
    }

    /**
     * Tear down all event listeners. Call when the form is removed from DOM.
     */
    destroy() {
      const { onKeydown, onInput, onFocus, onPaste, onSubmit } = this._boundHandlers;
      this.form.removeEventListener('keydown', onKeydown, true);
      this.form.removeEventListener('input', onInput, true);
      this.form.removeEventListener('focus', onFocus, true);
      this.form.removeEventListener('paste', onPaste, true);
      this.form.removeEventListener('submit', onSubmit);
    }

    // ─── Internals ───────────────────────────────────────────────────────────

    _fieldKey(el) {
      return el.name || el.id || el.getAttribute('data-fg-id') || (() => {
        const id = 'fg_' + Math.random().toString(36).slice(2, 8);
        el.setAttribute('data-fg-id', id);
        return id;
      })();
    }

    _notifyChange() {
      if (this._onChange) {
        const { score, signals } = this.calculateRiskScore();
        this._onChange(score, signals);
      }
    }
  }

  // ─── Export ───────────────────────────────────────────────────────────────

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormGuard;
  } else {
    global.FormGuard = FormGuard;
  }
})(typeof globalThis !== 'undefined' ? globalThis : window);
