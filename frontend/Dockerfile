FROM node:20-alpine AS build

WORKDIR /frontend

COPY package.json .npmrc vite.config.js index.html ./
COPY src ./src
RUN npm install
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /frontend/dist /usr/share/nginx/html

EXPOSE 80
