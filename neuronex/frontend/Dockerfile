FROM node:20-slim

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

EXPOSE 3001

# Vite dev server — binds to 0.0.0.0 so Docker port mapping works
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3001"]
