import '@testing-library/jest-dom';

// Mock scrollIntoView which is not implemented in JSDOM
window.HTMLElement.prototype.scrollIntoView = function() {};
