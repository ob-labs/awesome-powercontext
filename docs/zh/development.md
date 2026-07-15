# 开发

在仓库根目录运行后端检查：

```bash
make install-backend
make test-backend
make lint-backend
```

在场景前端目录运行前端检查：

```bash
cd scenarios/smart-ev-cockpit/frontend
npm install
npm test -- --run
npm run lint
npm run build
```

启动后端：

```bash
make backend
```

启动前端：

```bash
make frontend
```

默认 API 地址是 `http://127.0.0.1:8000`，默认 Vite 地址是 `http://127.0.0.1:5173`。
