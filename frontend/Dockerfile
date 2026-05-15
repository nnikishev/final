FROM node:22-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ENV VITE_API_URL=http://localhost:8000

RUN npm run build

EXPOSE 4173

CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "4173"]
