import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  appType: 'mpa',
  plugins: [
    {
      name: 'spanduk-mading- clean-url',
      configureServer(server) {
        server.middlewares.use((req, _res, next) => {
          if (req.url) {
            const [pathname, search] = req.url.split('?');
            if (pathname === '/spanduk-mading' || pathname === '/spanduk-mading/') {
              req.url = '/spanduk-mading/index.html' + (search ? `?${search}` : '');
            }
          }
          next();
        });
      },
      configurePreviewServer(server) {
        server.middlewares.use((req, _res, next) => {
          if (req.url) {
            const [pathname, search] = req.url.split('?');
            if (pathname === '/spanduk-mading' || pathname === '/spanduk-mading/') {
              req.url = '/spanduk-mading/index.html' + (search ? `?${search}` : '');
            }
          }
          next();
        });
      },
    },
  ],
  build: {
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
        spanduk: resolve(import.meta.dirname, 'spanduk-mading/index.html'),
      },
    },
  },
});
