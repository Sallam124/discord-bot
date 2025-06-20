# Use official Node.js 18 image
FROM node:18

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json ./

# Install dependencies
RUN npm install --production

# Copy the rest of the code
COPY . .

# Expose no ports (Discord bots do not need to expose ports)

# Start the bot
CMD ["npm", "start"] 