import '@testing-library/jest-dom';

// Polyfill scrollIntoView for jsdom environment
if (typeof window !== 'undefined') {
  window.HTMLElement.prototype.scrollIntoView = function() {};
}
