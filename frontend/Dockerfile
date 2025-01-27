# Production build
FROM node:18-bullseye AS build

WORKDIR /app

ENV PATH=/usr/local/bin:$PATH

COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build

# Use a small web server to serve the built files
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]