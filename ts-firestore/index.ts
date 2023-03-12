import {getArgs} from "./src/io";
import * as fs from "fs";
import * as path from "path";
import {getJobs} from "./src/db";

const args = getArgs();

(async () => {
    console.log("# 1. Read Parameter")
    if (args['path'] === undefined) return;

    const inFilename = path.join(path.normalize(<string>args['path']), "firestore.json");
    const outFilename = path.join(path.normalize(<string>args['path']), "guild_jobs.json");

    console.log(`# 2. read '${inFilename}'`)
    const config = JSON.parse(
        fs.readFileSync(inFilename, {encoding: "utf8", flag: 'r'} )
    );

    let token = config['token'],
        guildId = config['guildId'],
        firebaseConfig = config['firebaseConfig'];
    console.log(config);

    console.log(`# 3. await getJobs(token, guildId, firebaseConfig)`)
    let output = await getJobs(token, guildId, firebaseConfig);
    console.log(output);

    console.log(`# 4. write file.`)
    fs.writeFileSync(outFilename, output, {encoding: 'utf8', flag:'w'});
    console.log(`# 5. end.`)
    process.exit(0);
})();
