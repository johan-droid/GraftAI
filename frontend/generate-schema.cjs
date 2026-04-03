const { auth } = require('./src/lib/auth-server.js');
const fs = require('fs');

async function main() {
    try {
        const schema = await auth.db.generateSchema();
        fs.writeFileSync('schema.sql', schema);
        console.log('Schema generated to schema.sql');
    } catch (e) {
        console.error('Error generating schema:', e);
        process.exit(1);
    }
}
main();
